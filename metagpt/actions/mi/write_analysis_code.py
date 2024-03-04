# -*- encoding: utf-8 -*-
"""
@Date    :   2023/11/20 13:19:39
@Author  :   orange-crow
@File    :   write_analysis_code.py
"""
from __future__ import annotations

import json
from typing import Tuple

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.prompts.mi.ml_action import MODEL_TRAIN_EXAMPLE, USE_ML_TOOLS_EXAMPLE
from metagpt.prompts.mi.write_analysis_code import (
    CHECK_DATA_PROMPT,
    DEBUG_REFLECTION_EXAMPLE,
    REFLECTION_PROMPT,
    STRUCTUAL_PROMPT,
    TOOL_RECOMMENDATION_PROMPT,
)
from metagpt.schema import Message, Plan
from metagpt.tools import TOOL_REGISTRY
from metagpt.tools.tool_registry import validate_tool_names
from metagpt.tools.tool_type import ToolType
from metagpt.utils.common import CodeParser, process_message, remove_comments


class WriteCodeWithTools(Action):
    """Write code with help of local available tools. Choose tools first, then generate code to use the tools"""

    use_tools: bool = True
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
        rsp = await self._aask(prompt)
        rsp = CodeParser.parse_code(block=None, text=rsp)
        recommend_tools = json.loads(rsp)
        logger.info(f"Recommended tools: \n{recommend_tools}")

        # Parses and validates the  recommended tools, for LLM might hallucinate and recommend non-existing tools
        valid_tools = validate_tool_names(recommend_tools, return_tool_object=True)

        tool_schemas = {tool.name: tool.schemas for tool in valid_tools}

        return tool_schemas

    async def _prepare_tools(self, plan: Plan) -> Tuple[dict, str, str]:
        """Prepare tool schemas and usage instructions according to current task

        Args:
            plan (Plan): The overall plan containing task information.

        Returns:
            Tuple[dict, str, str]: A tool schemas ({tool_name: tool_schema_dict}), a usage prompt for the type of tools selected, and examples of using the tools
        """
        if not self.use_tools:
            return {}, "", ""

        # find tool type from task type through exact match, can extend to retrieval in the future
        tool_type = plan.current_task.task_type

        # prepare tool-type-specific instruction
        tool_type_usage_prompt = (
            TOOL_REGISTRY.get_tool_type(tool_type).usage_prompt if TOOL_REGISTRY.has_tool_type(tool_type) else ""
        )

        # ML-specific tool usage examples
        examples = ""
        if plan.current_task.task_type in [
            ToolType.DATA_PREPROCESS.type_name,
            ToolType.FEATURE_ENGINEERING.type_name,
        ]:
            examples = USE_ML_TOOLS_EXAMPLE
        elif plan.current_task.task_type in [ToolType.MODEL_TRAIN.type_name]:
            examples = MODEL_TRAIN_EXAMPLE

        # prepare schemas of available tools
        tool_schemas = {}
        available_tools = self._get_tools_by_type(tool_type)
        if available_tools:
            available_tools = {tool_name: tool.schemas["description"] for tool_name, tool in available_tools.items()}
            tool_schemas = await self._recommend_tool(plan.current_task.instruction, available_tools)

        return tool_schemas, tool_type_usage_prompt, examples

    async def _debug_with_reflection(self, context: list[Message], working_memory: list[Message]):
        reflection_prompt = REFLECTION_PROMPT.format(
            debug_example=DEBUG_REFLECTION_EXAMPLE,
            context=context,
            previous_impl=working_memory,
        )
        # print(reflection_prompt)
        system_prompt = "You are an AI Python assistant. You will be given your previous implementation code of a task, runtime error results, and a hint to change the implementation appropriately. Write your full implementation "

        rsp = await self._aask(reflection_prompt, system_msgs=[system_prompt])
        reflection = json.loads(CodeParser.parse_code(block=None, text=rsp))

        return reflection["improved_impl"]

    async def run(
        self,
        plan: Plan,
        working_memory: list[Message] = [],
        use_reflection: bool = False,
        **kwargs,
    ) -> str:
        # prepare tool schemas and tool-type-specific instruction
        tool_schemas, tool_type_usage_prompt, examples = await self._prepare_tools(plan=plan)

        # necessary components to be used in prompt
        finished_tasks = plan.get_finished_tasks()
        code_written = [remove_comments(task.code) for task in finished_tasks]
        code_written = "\n\n".join(code_written)
        task_results = [task.result for task in finished_tasks]
        task_results = "\n\n".join(task_results)

        # structure prompt
        structual_prompt = STRUCTUAL_PROMPT.format(
            user_requirement=plan.goal,
            code_written=code_written,
            task_results=task_results,
            current_task=plan.current_task.instruction,
            tool_type_usage_prompt=tool_type_usage_prompt,
            tool_schemas=tool_schemas,
            examples=examples,
        )
        context = [Message(content=structual_prompt, role="user")] + working_memory
        context = process_message(context)

        # temp = context + working_memory
        # print(*temp, sep="***\n\n***")

        # LLM call
        if not use_reflection:
            rsp = await self.llm.aask(context, **kwargs)
            code = CodeParser.parse_code(block=None, text=rsp)

        else:
            code = await self._debug_with_reflection(context=context, working_memory=working_memory)

        return code


class CheckData(Action):
    async def run(self, plan: Plan = None) -> dict:
        finished_tasks = plan.get_finished_tasks()
        code_written = [remove_comments(task.code) for task in finished_tasks]
        code_written = "\n\n".join(code_written)
        prompt = CHECK_DATA_PROMPT.format(code_written=code_written)
        rsp = await self._aask(prompt)
        code = CodeParser.parse_code(block=None, text=rsp)
        return code
