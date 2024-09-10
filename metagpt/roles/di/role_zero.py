from __future__ import annotations

import inspect
import json
import re
import traceback
from datetime import datetime
from typing import Annotated, Callable, Dict, List, Literal, Optional, Tuple

from pydantic import Field, model_validator

from metagpt.actions import Action, UserRequirement
from metagpt.actions.analyze_requirements import AnalyzeRequirementsRestrictions
from metagpt.actions.di.run_command import RunCommand
from metagpt.actions.search_enhanced_qa import SearchEnhancedQA
from metagpt.const import IMAGES
from metagpt.exp_pool import exp_cache
from metagpt.exp_pool.context_builders import RoleZeroContextBuilder
from metagpt.exp_pool.serializers import RoleZeroSerializer
from metagpt.logs import logger
from metagpt.memory.role_zero_memory import RoleZeroLongTermMemory
from metagpt.prompts.di.role_zero import (
    ASK_HUMAN_COMMAND,
    CMD_PROMPT,
    JSON_REPAIR_PROMPT,
    QUICK_RESPONSE_SYSTEM_PROMPT,
    QUICK_THINK_EXAMPLES,
    QUICK_THINK_PROMPT,
    QUICK_THINK_SYSTEM_PROMPT,
    REGENERATE_PROMPT,
    REPORT_TO_HUMAN_PROMPT,
    ROLE_INSTRUCTION,
    SUMMARY_PROMPT,
    SYSTEM_PROMPT,
)
from metagpt.roles import Role
from metagpt.schema import AIMessage, LongTermMemoryItem, Message, UserMessage
from metagpt.strategy.experience_retriever import DummyExpRetriever, ExpRetriever
from metagpt.strategy.planner import Planner
from metagpt.tools.libs.browser import Browser
from metagpt.tools.libs.editor import Editor
from metagpt.tools.tool_recommend import BM25ToolRecommender, ToolRecommender
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import CodeParser, any_to_str, extract_and_encode_images
from metagpt.utils.exceptions import handle_exception
from metagpt.utils.repair_llm_raw_output import (
    RepairType,
    repair_escape_error,
    repair_llm_raw_output,
)
from metagpt.utils.report import ThoughtReporter


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
    special_tool_commands: list[str] = ["Plan.finish_current_task", "end", "Bash.run"]
    # List of exclusive tool commands.
    # If multiple instances of these commands appear, only the first occurrence will be retained.
    exclusive_tool_commands: list[str] = [
        "Editor.edit_file_by_replace",
        "Editor.insert_content_at_line",
        "Editor.append_file",
    ]
    # Equipped with three basic tools by default for optional use
    editor: Editor = Editor(enable_auto_lint=True)
    browser: Browser = Browser()

    # Experience
    experience_retriever: Annotated[ExpRetriever, Field(exclude=True)] = DummyExpRetriever()

    # Others
    command_rsp: str = ""  # the raw string containing the commands
    commands: list[dict] = []  # commands to be executed
    memory_k: int = 200  # number of memories (messages) to use as historical context
    enable_longterm_memory: bool = True  # whether to use longterm memory
    longterm_memory: RoleZeroLongTermMemory = None
    use_fixed_sop: bool = False
    requirements_constraints: str = ""  # the constraints in user requirements
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
            "SearchEnhancedQA.run": SearchEnhancedQA().run,
        }
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
        """Set longterm memory.

        If enable_longterm_memory is True and longterm_memory is not set, set it.
        The role name will be used as the collection name.
        """

        if self.enable_longterm_memory and not self.longterm_memory:
            self.longterm_memory = RoleZeroLongTermMemory(collection_name=self.name.replace(" ", ""))

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
            self.planner.plan.goal = self._get_all_memories()[-1].content
            self.requirements_constraints = await AnalyzeRequirementsRestrictions().run(self.planner.plan.goal)

        ### 1. Experience ###
        example = self._retrieve_experience()

        ### 2. Plan Status ###
        plan_status, current_task = self._get_plan_status()

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
            requirements_constraints=self.requirements_constraints,
        )

        ### Recent Observation ###
        memory = self._fetch_memories()
        memory = await self.parse_browser_actions(memory)
        memory = self.parse_images(memory)

        req = self.llm.format_msg(memory + [UserMessage(content=prompt)])
        state_data = dict(
            plan_status=plan_status,
            current_task=current_task,
            instruction=instruction,
        )
        async with ThoughtReporter(enable_llm_stream=True) as reporter:
            await reporter.async_report({"type": "react"})
            self.command_rsp = await self.llm_cached_aask(req=req, system_msgs=[system_prompt], state_data=state_data)
        self.command_rsp = await self._check_duplicates(req, self.command_rsp)

        return True

    @exp_cache(context_builder=RoleZeroContextBuilder(), serializer=RoleZeroSerializer())
    async def llm_cached_aask(self, *, req: list[dict], system_msgs: list[str], **kwargs) -> str:
        """Use `exp_cache` to automatically manage experiences.

        The `RoleZeroContextBuilder` attempts to add experiences to `req`.
        The `RoleZeroSerializer` extracts essential parts of `req` for the experience pool, trimming lengthy entries to retain only necessary parts.
        """
        return await self.llm.aask(req, system_msgs=system_msgs)

    async def parse_browser_actions(self, memory: list[Message]) -> list[Message]:
        if not self.browser.is_empty_page:
            pattern = re.compile(r"Command Browser\.(\w+) executed")
            for index, msg in zip(range(len(memory), 0, -1), memory[::-1]):
                if pattern.search(msg.content):
                    memory.insert(index, UserMessage(cause_by="browser", content=await self.browser.view()))
                    break
        return memory

    def parse_images(self, memory: list[Message]) -> list[Message]:
        if not self.llm.support_image_input():
            return memory
        for msg in memory:
            if IMAGES in msg.metadata or msg.role != "user":
                continue
            images = extract_and_encode_images(msg.content)
            if images:
                msg.add_metadata(IMAGES, images)
        return memory

    def _get_prefix(self) -> str:
        time_info = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return super()._get_prefix() + f" The current time is {time_info}."

    async def _act(self) -> Message:
        if self.use_fixed_sop:
            return await super()._act()

        commands, ok, self.command_rsp = await self._parse_commands(self.command_rsp)
        self._add_memory(AIMessage(content=self.command_rsp))
        if not ok:
            error_msg = commands
            self._add_memory(UserMessage(content=error_msg, cause_by=RunCommand))
            return error_msg
        logger.info(f"Commands: \n{commands}")
        outputs = await self._run_commands(commands)
        logger.info(f"Commands outputs: \n{outputs}")
        self._add_memory(UserMessage(content=outputs, cause_by=RunCommand))

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
                rsp = await self.ask_human("I have reached my max action rounds, do you want me to continue? Yes or no")
                if "yes" in rsp.lower():
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
        memory = self._fetch_memories()
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
            self._add_memory(AIMessage(content=answer, cause_by=RunCommand))
            await self.reply_to_human(content=answer)
            rsp_msg = AIMessage(
                content="Complete run",
                sent_from=self.name,
                cause_by=RunCommand,
            )

        return rsp_msg, intent_result

    async def _check_duplicates(self, req: list[dict], command_rsp: str):
        past_rsp = [mem.content for mem in self._fetch_memories()]
        if command_rsp in past_rsp:
            # Normal response with thought contents are highly unlikely to reproduce
            # If an identical response is detected, it is a bad response, mostly due to LLM repeating generated content
            # In this case, ask human for help and regenerate
            # TODO: switch to llm_cached_aask

            #  Hard rule to ask human for help
            if past_rsp.count(command_rsp) >= 3:
                return ASK_HUMAN_COMMAND
            # Try correction by self
            logger.warning(f"Duplicate response detected: {command_rsp}")
            regenerate_req = req + [UserMessage(content=REGENERATE_PROMPT)]
            regenerate_req = self.llm.format_msg(regenerate_req)
            command_rsp = await self.llm.aask(regenerate_req)
        return command_rsp

    async def _parse_commands(self, command_rsp) -> Tuple[List[Dict], bool]:
        """Retrieves commands from the Large Language Model (LLM).

        This function attempts to retrieve a list of commands from the LLM by
        processing the response (`self.command_rsp`). It handles potential errors
        during parsing and LLM response formats.

        Returns:
            A tuple containing:
                - A boolean flag indicating success (True) or failure (False).
        """
        try:
            commands = CodeParser.parse_code(block=None, lang="json", text=command_rsp)
            if commands.endswith("]") and not commands.startswith("["):
                commands = "[" + commands
            commands = json.loads(repair_llm_raw_output(output=commands, req_keys=[None], repair_type=RepairType.JSON))
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON for: {command_rsp}. Trying to repair...")
            commands = await self.llm.aask(
                msg=JSON_REPAIR_PROMPT.format(json_data=command_rsp, json_decode_error=str(e))
            )
            try:
                commands = json.loads(CodeParser.parse_code(block=None, lang="json", text=commands))
            except json.JSONDecodeError:
                # repair escape error of code and math
                commands = CodeParser.parse_code(block=None, lang="json", text=command_rsp)
                new_command = repair_escape_error(commands)
                commands = json.loads(
                    repair_llm_raw_output(output=new_command, req_keys=[None], repair_type=RepairType.JSON)
                )
        except Exception as e:
            tb = traceback.format_exc()
            print(tb)
            error_msg = str(e)
            return error_msg, False, command_rsp

        # 为了对LLM不按格式生成进行容错
        if isinstance(commands, dict):
            commands = commands["commands"] if "commands" in commands else [commands]

        # Set the exclusive command flag to False.
        command_flag = [command["command_name"] not in self.exclusive_tool_commands for command in commands]
        if command_flag.count(False) > 1:
            # Keep only the first exclusive command
            index_of_first_exclusive = command_flag.index(False)
            commands = [
                cmd
                for index, cmd in enumerate(commands)
                if index == index_of_first_exclusive or cmd["command_name"] not in self.exclusive_tool_commands
            ]
            command_rsp = "```json\n" + json.dumps(commands, indent=4, ensure_ascii=False) + "\n```json"
            logger.info(
                "exclusive command more than one in current command list. change the command list.\n" + command_rsp
            )
        return commands, True, command_rsp

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

        # output from bash.run may be empty, add decorations to the output to ensure visibility.
        elif cmd["command_name"] == "Bash.run":
            tool_obj = self.tool_execution_map[cmd["command_name"]]
            tool_output = await tool_obj(**cmd["args"])
            if len(tool_output) <= 10:
                command_output += (
                    f"\n[command]: {cmd['args']['cmd']} \n[command output] : {tool_output} (pay attention to this.)"
                )
            else:
                command_output += f"\n[command]: {cmd['args']['cmd']} \n[command output] : {tool_output}"

        return command_output

    def _get_plan_status(self) -> Tuple[str, str]:
        plan_status = self.planner.plan.model_dump(include=["goal", "tasks"])
        current_task = (
            self.planner.plan.current_task.model_dump(exclude=["code", "result", "is_success"])
            if self.planner.plan.current_task
            else ""
        )
        # format plan status
        # Example:
        # [GOAL] create a 2048 game
        # [TASK_ID 1] (finished) Create a Product Requirement Document (PRD) for the 2048 game. This task depends on tasks[]. [Assign to Alice]
        # [TASK_ID 2] (        ) Design the system architecture for the 2048 game. This task depends on tasks[1]. [Assign to Bob]
        formatted_plan_status = f"[GOAL] {plan_status['goal']}\n"
        if len(plan_status["tasks"]) > 0:
            formatted_plan_status += "[Plan]\n"
            for task in plan_status["tasks"]:
                formatted_plan_status += f"[TASK_ID {task['task_id']}] ({'finished' if task['is_finished'] else '    '}){task['instruction']} This task depends on tasks{task['dependent_task_ids']}. [Assign to {task['assignee']}]\n"
        else:
            formatted_plan_status += "No Plan \n"
        return formatted_plan_status, current_task

    def _retrieve_experience(self) -> str:
        """Default implementation of experience retrieval. Can be overwritten in subclasses."""
        context = [str(msg) for msg in self._fetch_memories()]
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
        memory = self._fetch_memories()
        # Ensure reply to the human before the "end" command is executed. Hard code k=5 for checking.
        if not any(["reply_to_human" in memory.content for memory in self._fetch_memories(k=5)]):
            logger.info("manually reply to human")
            pattern = r"\[Language Restrictions\](.*?)\n"
            match = re.search(pattern, self.requirements_constraints, re.DOTALL)
            reply_to_human_prompt = REPORT_TO_HUMAN_PROMPT.format(lanaguge_restruction=match.group(0) if match else "")
            async with ThoughtReporter(enable_llm_stream=True) as reporter:
                await reporter.async_report({"type": "quick"})
                reply_content = await self.llm.aask(self.llm.format_msg(memory + [UserMessage(reply_to_human_prompt)]))
            await self.reply_to_human(content=reply_content)
            self._add_memory(AIMessage(content=reply_content, cause_by=RunCommand))
        outputs = ""
        # Summary of the Completed Task and Deliverables
        if self.use_summary:
            logger.info("end current run and summarize")
            outputs = await self.llm.aask(self.llm.format_msg(memory + [UserMessage(SUMMARY_PROMPT)]))
        return outputs

    def _get_all_memories(self) -> list[Message]:
        return self._fetch_memories(k=0)

    def _fetch_memories(self, k: Optional[int] = None) -> list[Message]:
        """Fetches recent memories and optionally combines them with related long-term memories.

        If long-term memory is not enabled or the last message is not from the user,
        it returns the recent memories without fetching from long-term memory.

        Args:
            k (Optional[int]): The number of recent memories to fetch. If None, defaults to self.memory_k.

        Returns:
            List[Message]: A list of messages representing the combined memories.
        """

        if k is None:
            k = self.memory_k

        memories = self.rc.memory.get(k)

        if not self._should_use_longterm_memory(k=k, k_memories=memories):
            return memories

        query = self._build_longterm_memory_query(memories)
        related_memories = self.longterm_memory.fetch(query)
        logger.info(f"Fetched {len(related_memories)} long-term memories.")

        # Keep user and AI messages are paired.
        if self._is_first_message_from_ai(memories):
            memories.insert(0, self.rc.memory.get_by_position(-(k + 1)))

        final_memories = related_memories + memories

        return final_memories

    def _add_memory(self, message: Message):
        self.rc.memory.add(message)

        if not self._should_use_longterm_memory():
            return

        self._transfer_to_longterm_memory()

    def _should_use_longterm_memory(self, k: int = None, k_memories: list[Message] = None) -> bool:
        """Determines if long-term memory should be used.

        Long-term memory is used if:
        - k is not 0.
        - k_memories is None or k_memories is not empty, and the last message is a user message.
        - Long-term memory usage is enabled.
        - The count of recent memories is greater than self.memory_k.
        """

        conds = [
            k != 0,
            k_memories is None or self._is_last_message_from_user(k_memories),
            self.enable_longterm_memory,
            self.rc.memory.count() > self.memory_k,
        ]

        return all(conds)

    def _transfer_to_longterm_memory(self):
        item = self._get_longterm_memory_item()
        self.longterm_memory.add(item)

    @handle_exception
    def _get_longterm_memory_item(self) -> Optional[LongTermMemoryItem]:
        """Retrieves the most recent pair of user and AI messages before the last k messages."""

        index = -(self.memory_k + 1)
        message = self.rc.memory.get_by_position(index)
        if not message.is_ai_message():
            return None

        index = -(self.memory_k + 2)
        user_message = self.rc.memory.get_by_position(index)

        return LongTermMemoryItem(user_message=user_message, ai_message=message)

    def _is_last_message_from_user(self, memories: list[Message]) -> bool:
        return bool(memories and memories[-1].is_user_message())

    def _is_first_message_from_ai(self, memories: list[Message]) -> bool:
        return bool(memories and memories[0].is_ai_message())

    def _build_longterm_memory_query(self, memories: list[Message]) -> str:
        """Build the content used to query related long-term memory.

        Default is to get the most recent user message, or an empty string if none is found.
        """

        return next((m.content for m in reversed(memories) if m.is_real_user_message()), "")
