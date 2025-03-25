from __future__ import annotations

import inspect
import json
import re
import traceback
from datetime import datetime
from typing import Annotated, Callable, Literal, Optional, Tuple

from pydantic import Field, model_validator

from metagpt.actions import Action, UserRequirement
from metagpt.actions.di.run_command import RunCommand
from metagpt.actions.search_enhanced_qa import SearchEnhancedQA
from metagpt.exp_pool import exp_cache
from metagpt.exp_pool.context_builders import RoleZeroContextBuilder
from metagpt.exp_pool.serializers import RoleZeroSerializer
from metagpt.logs import logger
from metagpt.memory.role_zero_memory import RoleZeroLongTermMemory
from metagpt.prompts.di.role_zero import (
    CMD_PROMPT,
    DETECT_LANGUAGE_PROMPT,
    QUICK_RESPONSE_SYSTEM_PROMPT,
    QUICK_THINK_EXAMPLES,
    QUICK_THINK_PROMPT,
    QUICK_THINK_SYSTEM_PROMPT,
    QUICK_THINK_TAG,
    REPORT_TO_HUMAN_PROMPT,
    ROLE_INSTRUCTION,
    SUMMARY_PROMPT,
    SYSTEM_PROMPT,
)
from metagpt.roles import Role
from metagpt.schema import AIMessage, Message, UserMessage
from metagpt.strategy.experience_retriever import DummyExpRetriever, ExpRetriever
from metagpt.strategy.planner import Planner
from metagpt.tools.libs.browser import Browser
from metagpt.tools.libs.editor import Editor
from metagpt.tools.tool_recommend import BM25ToolRecommender, ToolRecommender
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import any_to_str
from metagpt.utils.report import ThoughtReporter
from metagpt.utils.role_zero_utils import (
    check_duplicates,
    format_terminal_output,
    get_plan_status,
    parse_browser_actions,
    parse_commands,
    parse_editor_result,
    parse_images,
)


@register_tool(include_functions=["ask_human", "reply_to_human"])
class RoleZero(Role):
    """A role who can think and act dynamically"""

    # Basic Info
    name: str = "Zero"
    profile: str = "RoleZero"
    goal: str = ""
    system_msg: Optional[list[str]] = None  # Use None to conform to the default value at llm.aask
    system_prompt: str = SYSTEM_PROMPT  # Use None to conform to the default value at llm.aask
    cmd_prompt: str = CMD_PROMPT
    cmd_prompt_current_state: str = ""
    instruction: str = ROLE_INSTRUCTION
    task_type_desc: Optional[str] = None

    # React Mode
    react_mode: Literal["react"] = "react"
    max_react_loop: int = 50  # used for react mode

    # Tools
    tools: list[str] = []  # Use special symbol ["<all>"] to indicate use of all registered tools
    tool_recommender: Optional[ToolRecommender] = None
    tool_execution_map: Annotated[dict[str, Callable], Field(exclude=True)] = {}
    special_tool_commands: list[str] = ["Plan.finish_current_task", "end", "Terminal.run_command", "RoleZero.ask_human"]
    # List of exclusive tool commands.
    # If multiple instances of these commands appear, only the first occurrence will be retained.
    exclusive_tool_commands: list[str] = [
        "Editor.edit_file_by_replace",
        "Editor.insert_content_at_line",
        "Editor.append_file",
        "Editor.open_file",
    ]
    # Equipped with three basic tools by default for optional use
    editor: Editor = Editor(enable_auto_lint=True)
    browser: Browser = Browser()

    # Experience
    experience_retriever: Annotated[ExpRetriever, Field(exclude=True)] = DummyExpRetriever()

    # Others
    observe_all_msg_from_buffer: bool = True
    command_rsp: str = ""  # the raw string containing the commands
    commands: list[dict] = []  # commands to be executed
    memory_k: int = 200  # number of memories (messages) to use as historical context
    use_fixed_sop: bool = False
    respond_language: str = ""  # Language for responding humans and publishing messages.
    use_summary: bool = True  # whether to summarize at the end

    @model_validator(mode="after")
    def set_plan_and_tool(self) -> "RoleZero":
        # We force using this parameter for DataAnalyst
        assert self.react_mode == "react"

        # Roughly the same part as DataInterpreter.set_plan_and_tool
        self._set_react_mode(react_mode=self.react_mode, max_react_loop=self.max_react_loop)
        if self.tools and not self.tool_recommender:
            self.tool_recommender = BM25ToolRecommender(tools=self.tools, force=True)
        self.set_actions([RunCommand])

        # HACK: Init Planner, control it through dynamic thinking; Consider formalizing as a react mode
        self.planner = Planner(goal="", working_memory=self.rc.working_memory, auto_run=True)

        return self

    @model_validator(mode="after")
    def set_tool_execution(self) -> "RoleZero":
        # default map
        self.tool_execution_map = {
            "Plan.append_task": self.planner.plan.append_task,
            "Plan.reset_task": self.planner.plan.reset_task,
            "Plan.replace_task": self.planner.plan.replace_task,
            "RoleZero.ask_human": self.ask_human,
            "RoleZero.reply_to_human": self.reply_to_human,
        }
        if self.config.enable_search:
            self.tool_execution_map["SearchEnhancedQA.run"] = SearchEnhancedQA().run
        self.tool_execution_map.update(
            {
                f"Browser.{i}": getattr(self.browser, i)
                for i in [
                    "click",
                    "close_tab",
                    "go_back",
                    "go_forward",
                    "goto",
                    "hover",
                    "press",
                    "scroll",
                    "tab_focus",
                    "type",
                ]
            }
        )
        self.tool_execution_map.update(
            {
                f"Editor.{i}": getattr(self.editor, i)
                for i in [
                    "append_file",
                    "create_file",
                    "edit_file_by_replace",
                    "find_file",
                    "goto_line",
                    "insert_content_at_line",
                    "open_file",
                    "read",
                    "scroll_down",
                    "scroll_up",
                    "search_dir",
                    "search_file",
                    "similarity_search",
                    # "set_workdir",
                    "write",
                ]
            }
        )
        # can be updated by subclass
        self._update_tool_execution()
        return self

    @model_validator(mode="after")
    def set_longterm_memory(self) -> "RoleZero":
        """Set up long-term memory for the role if enabled in the configuration.

        If `enable_longterm_memory` is True, set up long-term memory.
        The role name will be used as the collection name.
        """

        if self.config.role_zero.enable_longterm_memory:
            # Use config.role_zero to initialize long-term memory
            self.rc.memory = RoleZeroLongTermMemory(
                **self.rc.memory.model_dump(),
                persist_path=self.config.role_zero.longterm_memory_persist_path,
                collection_name=self.name.replace(" ", ""),
                memory_k=self.config.role_zero.memory_k,
                similarity_top_k=self.config.role_zero.similarity_top_k,
                use_llm_ranker=self.config.role_zero.use_llm_ranker,
            )
            logger.info(f"Long-term memory set for role '{self.name}'")

        return self

    def _update_tool_execution(self):
        pass

    async def _think(self) -> bool:
        """Useful in 'react' mode. Use LLM to decide whether and what to do next."""
        # Compatibility
        if self.use_fixed_sop:
            return await super()._think()

        ### 0. Preparation ###
        if not self.rc.todo:
            return False

        if not self.planner.plan.goal:
            self.planner.plan.goal = self.get_memories()[-1].content
            detect_language_prompt = DETECT_LANGUAGE_PROMPT.format(requirement=self.planner.plan.goal)
            self.respond_language = await self.llm.aask(detect_language_prompt)
        ### 1. Experience ###
        example = self._retrieve_experience()

        ### 2. Plan Status ###
        plan_status, current_task = get_plan_status(planner=self.planner)

        ### 3. Tool/Command Info ###
        tools = await self.tool_recommender.recommend_tools()
        tool_info = json.dumps({tool.name: tool.schemas for tool in tools})

        ### Role Instruction ###
        instruction = self.instruction.strip()
        system_prompt = self.system_prompt.format(
            role_info=self._get_prefix(),
            task_type_desc=self.task_type_desc,
            available_commands=tool_info,
            example=example,
            instruction=instruction,
        )

        ### Make Decision Dynamically ###
        prompt = self.cmd_prompt.format(
            current_state=self.cmd_prompt_current_state,
            plan_status=plan_status,
            current_task=current_task,
            respond_language=self.respond_language,
        )

        ### Recent Observation ###
        memory = self.rc.memory.get(self.memory_k)
        memory = await parse_browser_actions(memory, browser=self.browser)
        memory = await parse_editor_result(memory)
        memory = await parse_images(memory, llm=self.llm)

        req = self.llm.format_msg(memory + [UserMessage(content=prompt)])
        state_data = dict(
            plan_status=plan_status,
            current_task=current_task,
            instruction=instruction,
        )
        async with ThoughtReporter(enable_llm_stream=True) as reporter:
            await reporter.async_report({"type": "react"})
            self.command_rsp = await self.llm_cached_aask(req=req, system_msgs=[system_prompt], state_data=state_data)

        rsp_hist = [mem.content for mem in self.rc.memory.get()]
        self.command_rsp = await check_duplicates(
            req=req,
            command_rsp=self.command_rsp,
            rsp_hist=rsp_hist,
            llm=self.llm,
            respond_language=self.respond_language,
        )

        return True

    @exp_cache(context_builder=RoleZeroContextBuilder(), serializer=RoleZeroSerializer())
    async def llm_cached_aask(self, *, req: list[dict], system_msgs: list[str], **kwargs) -> str:
        """Use `exp_cache` to automatically manage experiences.

        The `RoleZeroContextBuilder` attempts to add experiences to `req`.
        The `RoleZeroSerializer` extracts essential parts of `req` for the experience pool, trimming lengthy entries to retain only necessary parts.
        """
        return await self.llm.aask(req, system_msgs=system_msgs)

    def _get_prefix(self) -> str:
        time_info = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return super()._get_prefix() + f" The current time is {time_info}."

    async def _act(self) -> Message:
        if self.use_fixed_sop:
            return await super()._act()

        commands, ok, self.command_rsp = await parse_commands(
            command_rsp=self.command_rsp, llm=self.llm, exclusive_tool_commands=self.exclusive_tool_commands
        )
        self.rc.memory.add(AIMessage(content=self.command_rsp))
        if not ok:
            error_msg = commands
            self.rc.memory.add(UserMessage(content=error_msg, cause_by=RunCommand))
            return error_msg
        logger.info(f"Commands: \n{commands}")
        outputs = await self._run_commands(commands)
        logger.info(f"Commands outputs: \n{outputs}")
        self.rc.memory.add(UserMessage(content=outputs, cause_by=RunCommand))

        return AIMessage(
            content=f"I have finished the task, please mark my task as finished. Outputs: {outputs}",
            sent_from=self.name,
            cause_by=RunCommand,
        )

    async def _react(self) -> Message:
        # NOTE: Diff 1: Each time landing here means news is observed, set todo to allow news processing in _think
        self._set_state(0)

        # problems solvable by quick thinking doesn't need to a formal think-act cycle
        quick_rsp, _ = await self._quick_think()
        if quick_rsp:
            return quick_rsp

        actions_taken = 0
        rsp = AIMessage(content="No actions taken yet", cause_by=Action)  # will be overwritten after Role _act
        while actions_taken < self.rc.max_react_loop:
            # NOTE: Diff 2: Keep observing within _react, news will go into memory, allowing adapting to new info
            await self._observe()

            # think
            has_todo = await self._think()
            if not has_todo:
                break
            # act
            logger.debug(f"{self._setting}: {self.rc.state=}, will do {self.rc.todo}")
            rsp = await self._act()
            actions_taken += 1

            # post-check
            if self.rc.max_react_loop >= 10 and actions_taken >= self.rc.max_react_loop:
                # If max_react_loop is a small value (e.g. < 10), it is intended to be reached and make the agent stop
                logger.warning(f"reached max_react_loop: {actions_taken}")
                human_rsp = await self.ask_human(
                    "I have reached my max action rounds, do you want me to continue? Yes or no"
                )
                if "yes" in human_rsp.lower():
                    actions_taken = 0
        return rsp  # return output from the last action

    def format_quick_system_prompt(self) -> str:
        """Format the system prompt for quick thinking."""
        return QUICK_THINK_SYSTEM_PROMPT.format(examples=QUICK_THINK_EXAMPLES, role_info=self._get_prefix())

    async def _quick_think(self) -> Tuple[Message, str]:
        answer = ""
        rsp_msg = None
        if self.rc.news[-1].cause_by != any_to_str(UserRequirement):
            # Agents themselves won't generate quick questions, use this rule to reduce extra llm calls
            return rsp_msg, ""

        # routing
        memory = self.get_memories(k=self.memory_k)
        context = self.llm.format_msg(memory + [UserMessage(content=QUICK_THINK_PROMPT)])
        async with ThoughtReporter() as reporter:
            await reporter.async_report({"type": "classify"})
            intent_result = await self.llm.aask(context, system_msgs=[self.format_quick_system_prompt()])

        if "QUICK" in intent_result or "AMBIGUOUS" in intent_result:  # llm call with the original context
            async with ThoughtReporter(enable_llm_stream=True) as reporter:
                await reporter.async_report({"type": "quick"})
                answer = await self.llm.aask(
                    self.llm.format_msg(memory),
                    system_msgs=[QUICK_RESPONSE_SYSTEM_PROMPT.format(role_info=self._get_prefix())],
                )
            # If the answer contains the substring '[Message] from A to B:', remove it.
            pattern = r"\[Message\] from .+? to .+?:\s*"
            answer = re.sub(pattern, "", answer, count=1)
            if "command_name" in answer:
                # an actual TASK intent misclassified as QUICK, correct it here, FIXME: a better way is to classify it correctly in the first place
                answer = ""
                intent_result = "TASK"
        elif "SEARCH" in intent_result:
            query = "\n".join(str(msg) for msg in memory)
            answer = await SearchEnhancedQA().run(query)

        if answer:
            self.rc.memory.add(AIMessage(content=answer, cause_by=QUICK_THINK_TAG))
            await self.reply_to_human(content=answer)
            rsp_msg = AIMessage(
                content=answer,
                sent_from=self.name,
                cause_by=QUICK_THINK_TAG,
            )

        return rsp_msg, intent_result

    async def _run_commands(self, commands) -> str:
        outputs = []
        for cmd in commands:
            output = f"Command {cmd['command_name']} executed"
            # handle special command first
            if self._is_special_command(cmd):
                special_command_output = await self._run_special_command(cmd)
                outputs.append(output + ":" + special_command_output)
                continue
            # run command as specified by tool_execute_map
            if cmd["command_name"] in self.tool_execution_map:
                tool_obj = self.tool_execution_map[cmd["command_name"]]
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
                    logger.exception(str(e) + tb)
                    outputs.append(output + f": {tb}")
                    break  # Stop executing if any command fails
            else:
                outputs.append(f"Command {cmd['command_name']} not found.")
                break
        outputs = "\n\n".join(outputs)

        return outputs

    def _is_special_command(self, cmd) -> bool:
        return cmd["command_name"] in self.special_tool_commands

    async def _run_special_command(self, cmd) -> str:
        """command requiring special check or parsing"""
        command_output = ""

        if cmd["command_name"] == "Plan.finish_current_task":
            if not self.planner.plan.is_plan_finished():
                self.planner.plan.finish_current_task()
            command_output = (
                "Current task is finished. If you no longer need to take action, use the command ‘end’ to stop."
            )

        elif cmd["command_name"] == "end":
            command_output = await self._end()
        elif cmd["command_name"] == "RoleZero.ask_human":
            human_response = await self.ask_human(**cmd["args"])
            if human_response.strip().lower().endswith(("stop", "<stop>")):
                human_response += "The user has asked me to stop because I have encountered a problem."
                self.rc.memory.add(UserMessage(content=human_response, cause_by=RunCommand))
                end_output = "\nCommand end executed:"
                end_output += await self._end()
                return end_output
            return human_response
        # output from bash.run may be empty, add decorations to the output to ensure visibility.
        elif cmd["command_name"] == "Terminal.run_command":
            tool_obj = self.tool_execution_map[cmd["command_name"]]
            tool_output = await tool_obj(**cmd["args"])
            command_output = format_terminal_output(cmd=cmd, raw_output=tool_output)
        return command_output

    def _retrieve_experience(self) -> str:
        """Default implementation of experience retrieval. Can be overwritten in subclasses."""
        context = [str(msg) for msg in self.rc.memory.get(self.memory_k)]
        context = "\n\n".join(context)
        example = self.experience_retriever.retrieve(context=context)
        return example

    async def ask_human(self, question: str) -> str:
        """Use this when you fail the current task or if you are unsure of the situation encountered. Your response should contain a brief summary of your situation, ended with a clear and concise question."""
        # NOTE: Can be overwritten in remote setting
        from metagpt.environment.mgx.mgx_env import MGXEnv  # avoid circular import

        if not isinstance(self.rc.env, MGXEnv):
            return "Not in MGXEnv, command will not be executed."
        return await self.rc.env.ask_human(question, sent_from=self)

    async def reply_to_human(self, content: str) -> str:
        """Reply to human user with the content provided. Use this when you have a clear answer or solution to the user's question."""
        # NOTE: Can be overwritten in remote setting
        from metagpt.environment.mgx.mgx_env import MGXEnv  # avoid circular import

        if not isinstance(self.rc.env, MGXEnv):
            return "Not in MGXEnv, command will not be executed."
        return await self.rc.env.reply_to_human(content, sent_from=self)

    async def _end(self, **kwarg):
        self._set_state(-1)
        memory = self.rc.memory.get(self.memory_k)
        # Ensure reply to the human before the "end" command is executed. Hard code k=5 for checking.
        if not any(["reply_to_human" in memory.content for memory in self.get_memories(k=5)]):
            logger.info("manually reply to human")
            reply_to_human_prompt = REPORT_TO_HUMAN_PROMPT.format(respond_language=self.respond_language)
            async with ThoughtReporter(enable_llm_stream=True) as reporter:
                await reporter.async_report({"type": "quick"})
                reply_content = await self.llm.aask(self.llm.format_msg(memory + [UserMessage(reply_to_human_prompt)]))
            await self.reply_to_human(content=reply_content)
            self.rc.memory.add(AIMessage(content=reply_content, cause_by=RunCommand))
        outputs = ""
        # Summary of the Completed Task and Deliverables
        if self.use_summary:
            logger.info("end current run and summarize")
            outputs = await self.llm.aask(self.llm.format_msg(memory + [UserMessage(SUMMARY_PROMPT)]))
        return outputs
