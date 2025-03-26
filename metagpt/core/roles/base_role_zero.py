from __future__ import annotations

from datetime import datetime
from typing import Annotated, Callable, Literal, Optional

from pydantic import Field, model_validator

from metagpt.core.actions import Action
from metagpt.core.exp_pool import exp_cache
from metagpt.core.exp_pool.context_builders import RoleZeroContextBuilder
from metagpt.core.exp_pool.serializers import RoleZeroSerializer
from metagpt.core.logs import logger
from metagpt.core.memory.role_zero_memory import RoleZeroLongTermMemory
from metagpt.core.prompts.role_zero import (
    CMD_PROMPT,
    QUICK_THINK_EXAMPLES,
    QUICK_THINK_SYSTEM_PROMPT,
    ROLE_INSTRUCTION,
    SYSTEM_PROMPT,
)
from metagpt.core.roles.role import Role
from metagpt.core.schema import AIMessage, Message
from metagpt.core.strategy.experience_retriever import DummyExpRetriever, ExpRetriever
from metagpt.core.tools.tool_recommend import ToolRecommender


class BaseRoleZero(Role):
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
    def set_plan_and_tool(self) -> "BaseRoleZero":
        """Initialize plan and tool related attributes"""
        return self

    @model_validator(mode="after")
    def set_tool_execution(self) -> "BaseRoleZero":
        """Initialize tool execution mapping"""
        return self

    @model_validator(mode="after")
    def set_longterm_memory(self) -> "BaseRoleZero":
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

    async def _think(self) -> bool:
        return super()._think()

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
        return await super()._act()

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

    async def _quick_think(self):
        pass

    def _is_special_command(self, cmd) -> bool:
        return cmd["command_name"] in self.special_tool_commands

    async def ask_human(self, question: str):
        raise NotImplementedError

    async def reply_to_human(self, content: str):
        raise NotImplementedError

    async def _end(self, **kwarg):
        pass
