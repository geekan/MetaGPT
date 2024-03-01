# -*- encoding: utf-8 -*-
"""
@Date    :   2023/11/20 13:19:39
@Author  :   orange-crow
@File    :   write_analysis_code.py
"""
from __future__ import annotations

from typing import Tuple

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.prompts.di.write_analysis_code import (
    CODE_GENERATOR_WITH_TOOLS,
    SELECT_FUNCTION_TOOLS,
    TOOL_RECOMMENDATION_PROMPT,
    TOOL_USAGE_PROMPT,
)
from metagpt.schema import Message, Plan, SystemMessage
from metagpt.tools import TOOL_REGISTRY
from metagpt.tools.tool_registry import validate_tool_names
from metagpt.utils.common import create_func_call_config


class BaseWriteAnalysisCode(Action):
    DEFAULT_SYSTEM_MSG: str = """You are Code Interpreter, a world-class programmer that can complete any goal by executing code. Strictly follow the plan and generate code step by step. Each step of the code will be executed on the user's machine, and the user will provide the code execution results to you.**Notice: The code for the next step depends on the code for the previous step. Must reuse variables in the lastest other code directly, dont creat it again, it is very import for you. Use !pip install in a standalone block to install missing packages.Usually the libraries you need are already installed.Dont check if packages already imported.**"""  # prompt reference: https://github.com/KillianLucas/open-interpreter/blob/v0.1.4/interpreter/system_message.txt
    # REUSE_CODE_INSTRUCTION = """ATTENTION: DONT include codes from previous tasks in your current code block, include new codes only, DONT repeat codes!"""

    def insert_system_message(self, context: list[Message], system_msg: str = None):
        system_msg = system_msg or self.DEFAULT_SYSTEM_MSG
        context.insert(0, SystemMessage(content=system_msg)) if context[0].role != "system" else None
        return context

    async def run(self, context: list[Message], plan: Plan = None) -> dict:
        """Run of a code writing action, used in data analysis or modeling

        Args:
            context (list[Message]): Action output history, source action denoted by Message.cause_by
            plan (Plan, optional): Overall plan. Defaults to None.

        Returns:
            dict: code result in the format of {"code": "print('hello world')", "language": "python"}
        """
        raise NotImplementedError


class WriteCodeWithoutTools(BaseWriteAnalysisCode):
    """Ask LLM to generate codes purely by itself without local user-defined tools"""

    async def run(self, context: list[Message], plan: Plan = None, system_msg: str = None, **kwargs) -> dict:
        messages = self.insert_system_message(context, system_msg)
        rsp = await self.llm.aask_code(messages, **kwargs)
        return rsp


class WriteCodeWithTools(BaseWriteAnalysisCode):
    """Write code with help of local available tools. Choose tools first, then generate code to use the tools"""

    # selected tools to choose from, listed by their names. An empty list means selection from all tools.
    selected_tools: list[str] = []

    def _get_tools_by_type(self, tool_type: str) -> dict:
        """
        Retreive tools by tool type from registry, but filtered by pre-selected tool list

        Args:
            tool_type (str): Tool type to retrieve from the registry

        Returns:
            dict: A dict of tool name to Tool object, representing available tools under the type
        """
        candidate_tools = TOOL_REGISTRY.get_tools_by_type(tool_type)
        if self.selected_tools:
            candidate_tool_names = set(self.selected_tools) & candidate_tools.keys()
            candidate_tools = {tool_name: candidate_tools[tool_name] for tool_name in candidate_tool_names}
        return candidate_tools

    async def _recommend_tool(
        self,
        task: str,
        available_tools: dict,
    ) -> dict:
        """
        Recommend tools for the specified task.

        Args:
            task (str): the task to recommend tools for
            available_tools (dict): the available tools description

        Returns:
            dict: schemas of recommended tools for the specified task
        """
        prompt = TOOL_RECOMMENDATION_PROMPT.format(
            current_task=task,
            available_tools=available_tools,
        )
        tool_config = create_func_call_config(SELECT_FUNCTION_TOOLS)
        rsp = await self.llm.aask_code(prompt, **tool_config)
        recommend_tools = rsp["recommend_tools"]
        logger.info(f"Recommended tools: \n{recommend_tools}")

        # Parses and validates the  recommended tools, for LLM might hallucinate and recommend non-existing tools
        valid_tools = validate_tool_names(recommend_tools, return_tool_object=True)

        tool_schemas = {tool.name: tool.schemas for tool in valid_tools}

        return tool_schemas

    async def _prepare_tools(self, plan: Plan) -> Tuple[dict, str]:
        """Prepare tool schemas and usage instructions according to current task

        Args:
            plan (Plan): The overall plan containing task information.

        Returns:
            Tuple[dict, str]: A tool schemas ({tool_name: tool_schema_dict}) and a usage prompt for the type of tools selected
        """
        # find tool type from task type through exact match, can extend to retrieval in the future
        tool_type = plan.current_task.task_type

        # prepare tool-type-specific instruction
        tool_type_usage_prompt = (
            TOOL_REGISTRY.get_tool_type(tool_type).usage_prompt if TOOL_REGISTRY.has_tool_type(tool_type) else ""
        )

        # prepare schemas of available tools
        tool_schemas = {}
        available_tools = self._get_tools_by_type(tool_type)
        if available_tools:
            available_tools = {tool_name: tool.schemas["description"] for tool_name, tool in available_tools.items()}
            tool_schemas = await self._recommend_tool(plan.current_task.instruction, available_tools)

        return tool_schemas, tool_type_usage_prompt

    async def run(
        self,
        context: list[Message],
        plan: Plan,
        **kwargs,
    ) -> str:
        # prepare tool schemas and tool-type-specific instruction
        tool_schemas, tool_type_usage_prompt = await self._prepare_tools(plan=plan)

        # form a complete tool usage instruction and include it as a message in context
        tools_instruction = TOOL_USAGE_PROMPT.format(
            tool_schemas=tool_schemas, tool_type_usage_prompt=tool_type_usage_prompt
        )
        context.append(Message(content=tools_instruction, role="user"))

        # prepare prompt & LLM call
        prompt = self.insert_system_message(context)
        tool_config = create_func_call_config(CODE_GENERATOR_WITH_TOOLS)
        rsp = await self.llm.aask_code(prompt, **tool_config)

        return rsp
