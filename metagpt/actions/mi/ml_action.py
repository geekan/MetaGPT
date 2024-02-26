from __future__ import annotations

from typing import Tuple

from metagpt.actions import Action
from metagpt.actions.mi.write_analysis_code import WriteCodeWithTools
from metagpt.prompts.mi.ml_action import (
    ML_PROMPT,
    UPDATE_DATA_COLUMNS,
    USE_NO_TOOLS_EXAMPLE,
    USE_TOOLS_EXAMPLE,
)
from metagpt.schema import Message, Plan
from metagpt.utils.common import remove_comments


class WriteCodeWithToolsML(WriteCodeWithTools):
    async def run(
        self,
        context: list[Message],
        plan: Plan = None,
        column_info: str = "",
        **kwargs,
    ) -> Tuple[list[Message], str]:
        # prepare tool schemas and tool-type-specific instruction
        tool_schemas, tool_type_usage_prompt = await self._prepare_tools(plan=plan)

        # ML-specific variables to be used in prompt
        finished_tasks = plan.get_finished_tasks()
        code_context = [remove_comments(task.code) for task in finished_tasks]
        code_context = "\n\n".join(code_context)

        # prepare prompt depending on tool availability & LLM call
        prompt = ML_PROMPT.format(
            user_requirement=plan.goal,
            history_code=code_context,
            current_task=plan.current_task.instruction,
            column_info=column_info,
            tool_type_usage_prompt=tool_type_usage_prompt,
            tool_schemas=tool_schemas,
            examples=USE_TOOLS_EXAMPLE if tool_schemas else USE_NO_TOOLS_EXAMPLE,
        )

        rsp = await self.llm.aask_code(prompt, language="python")

        # Extra output to be used for potential debugging
        context = [Message(content=prompt, role="user")]

        return context, rsp


class UpdateDataColumns(Action):
    async def run(self, plan: Plan = None) -> dict:
        finished_tasks = plan.get_finished_tasks()
        code_context = [remove_comments(task.code) for task in finished_tasks]
        code_context = "\n\n".join(code_context)
        prompt = UPDATE_DATA_COLUMNS.format(history_code=code_context)
        rsp = await self.llm.aask_code(prompt, language="python")
        return rsp
