from __future__ import annotations

import inspect
import json
import traceback
from typing import Literal

from pydantic import model_validator

from metagpt.actions import Action
from metagpt.actions.di.run_command import RunCommand
from metagpt.environment.mgx.mgx_env import MGXEnv
from metagpt.logs import logger
from metagpt.prompts.di.role_zero import CMD_PROMPT, ROLE_INSTRUCTION
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.strategy.experience_retriever import DummyExpRetriever, ExpRetriever
from metagpt.strategy.planner import Planner
from metagpt.tools.tool_recommend import BM25ToolRecommender, ToolRecommender
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import CodeParser


@register_tool(include_functions=["ask_human", "reply_to_human"])
class RoleZero(Role):
    """A role who can think and act dynamically"""

    # Basic Info
    name: str = "Zero"
    profile: str = "RoleZero"
    goal: str = ""
    system_msg: list[str] = None  # Use None to conform to the default value at llm.aask
    cmd_prompt: str = CMD_PROMPT
    instruction: str = ROLE_INSTRUCTION

    # React Mode
    react_mode: Literal["react"] = "react"
    max_react_loop: int = 20  # used for react mode

    # Tools
    tools: list[str] = []  # Use special symbol ["<all>"] to indicate use of all registered tools
    tool_recommender: ToolRecommender = None
    tool_execution_map: dict[str, callable] = {}
    special_tool_commands: list[str] = ["Plan.finish_current_task", "end"]

    # Experience
    experience_retriever: ExpRetriever = DummyExpRetriever()

    # Others
    user_requirement: str = ""
    command_rsp: str = ""  # the raw string containing the commands
    commands: list[dict] = []  # commands to be executed
    memory_k: int = 20  # number of memories (messages) to use as historical context
    use_fixed_sop: bool = False

    @model_validator(mode="after")
    def set_plan_and_tool(self) -> "RoleZero":
        # We force using this parameter for DataAnalyst
        assert self.react_mode == "react"

        # Roughly the same part as DataInterpreter.set_plan_and_tool
        self._set_react_mode(react_mode=self.react_mode, max_react_loop=self.max_react_loop)
        if self.tools and not self.tool_recommender:
            self.tool_recommender = BM25ToolRecommender(tools=self.tools, force=True)
        self.set_actions([RunCommand])
        self._set_state(0)

        # HACK: Init Planner, control it through dynamic thinking; Consider formalizing as a react mode
        self.planner = Planner(goal="", working_memory=self.rc.working_memory, auto_run=True)

        return self

    @model_validator(mode="after")
    def set_tool_execution(self) -> "RoleZero":
        raise NotImplementedError

    async def _think(self) -> bool:
        """Useful in 'react' mode. Use LLM to decide whether and what to do next."""
        # Compatibility
        if self.use_fixed_sop:
            return await super()._think()

        ### 0. Preparation ###
        if not self.rc.todo and not self.rc.news:
            return False
        self._set_state(0)
        if not self.planner.plan.goal:
            self.user_requirement = self.get_memories()[-1].content
            self.planner.plan.goal = self.user_requirement

        ### 1. Experience ###
        example = self._retrieve_experience()

        ### 2. Plan Status ###
        plan_status = self.planner.plan.model_dump(include=["goal", "tasks"])
        for task in plan_status["tasks"]:
            task.pop("code")
            task.pop("result")
            task.pop("is_success")
        # print(plan_status)
        current_task = (
            self.planner.plan.current_task.model_dump(exclude=["code", "result", "is_success"])
            if self.planner.plan.current_task
            else ""
        )

        ### 3. Tool/Command Info ###
        tools = await self.tool_recommender.recommend_tools()
        tool_info = json.dumps({tool.name: tool.schemas for tool in tools})

        ### Make Decision Dynamically ###
        prompt = self.cmd_prompt.format(
            plan_status=plan_status,
            current_task=current_task,
            example=example,
            available_commands=tool_info,
            instruction=self.instruction.strip(),
        )
        context = self.llm.format_msg(self.rc.memory.get(self.memory_k) + [Message(content=prompt, role="user")])
        print(*context, sep="\n" + "*" * 5 + "\n")
        self.command_rsp = await self.llm.aask(context, system_msgs=self.system_msg)
        self.rc.memory.add(Message(content=self.command_rsp, role="assistant"))

        return True

    async def _act(self) -> Message:
        if self.use_fixed_sop:
            return await super()._act()

        try:
            commands = json.loads(CodeParser.parse_code(block=None, lang="json", text=self.command_rsp))
        except Exception as e:
            tb = traceback.format_exc()
            print(tb)
            error_msg = Message(content=str(e), role="user")
            self.rc.memory.add(error_msg)
            return error_msg
        outputs = await self._run_commands(commands)
        self.rc.memory.add(Message(content=outputs, role="user"))
        return Message(
            content=f"Complete run with outputs: {outputs}",
            role="assistant",
            sent_from=self._setting,
            cause_by=RunCommand,
        )

    async def _react(self) -> Message:
        actions_taken = 0
        rsp = Message(content="No actions taken yet", cause_by=Action)  # will be overwritten after Role _act
        while actions_taken < self.rc.max_react_loop:
            # NOTE: difference here, keep observing within react
            await self._observe()
            # think
            has_todo = await self._think()
            if not has_todo:
                break
            # act
            logger.debug(f"{self._setting}: {self.rc.state=}, will do {self.rc.todo}")
            rsp = await self._act()
            actions_taken += 1
        return rsp  # return output from the last action

    async def _run_commands(self, commands) -> list:
        outputs = []
        for cmd in commands:
            # handle special command first
            if await self._run_special_command(cmd):
                continue
            # run command as specified by tool_execute_map
            if cmd["command_name"] in self.tool_execution_map:
                tool_obj = self.tool_execution_map[cmd["command_name"]]
                output = f"Command {cmd['command_name']} executed"
                try:
                    if inspect.iscoroutinefunction(tool_obj):
                        tool_output = await tool_obj(**cmd["args"])
                    else:
                        tool_output = tool_obj(**cmd["args"])
                    if tool_output:
                        output += f": {str(tool_output)}"
                    outputs.append(output)
                except Exception as e:
                    tb = traceback.format_exc()
                    print(e, tb)
                    outputs.append(output + f": {tb}")
                    break  # Stop executing if any command fails
            else:
                outputs.append(f"Command {cmd['command_name']} not found.")
                break
        outputs = "\n\n".join(outputs)

        return outputs

    async def _run_special_command(self, cmd) -> bool:
        """command requiring special check or parsing"""
        is_special_cmd = cmd["command_name"] in self.special_tool_commands

        if cmd["command_name"] == "Plan.finish_current_task" and not self.planner.plan.is_plan_finished():
            # task_result = TaskResult(code=str(commands), result=outputs, is_success=is_success)
            # self.planner.plan.current_task.update_task_result(task_result=task_result)
            self.planner.plan.finish_current_task()

        elif cmd["command_name"] == "end":
            self._set_state(-1)

        return is_special_cmd

    def _retrieve_experience(self) -> str:
        """Default implementation of experience retrieval. Can be overwritten in subclasses."""
        context = [str(msg) for msg in self.rc.memory.get(self.memory_k)]
        context = "\n\n".join(context)
        example = self.experience_retriever.retrieve(context=context)
        return example

    async def ask_human(self, question: str) -> str:
        """Use this when you fail the current task or if you are unsure of the situation encountered. Your response should contain a brief summary of your situation, ended with a clear and concise question."""
        # NOTE: Can be overwritten in remote setting
        if not isinstance(self.rc.env, MGXEnv):
            return "Not in MGXEnv, command will not be executed."
        return await self.rc.env.get_human_input(question, sent_from=self)

    async def reply_to_human(self, content: str) -> str:
        """Reply to human user with the content provided. Use this when you have a clear answer or solution to the user's question."""
        # NOTE: Can be overwritten in remote setting
        if not isinstance(self.rc.env, MGXEnv):
            return "Not in MGXEnv, command will not be executed."
        return await self.rc.env.reply_to_human(content, sent_from=self)
