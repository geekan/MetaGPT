from typing import List, Tuple

from metagpt.actions import Action
from metagpt.actions.write_analysis_code import WriteCodeWithTools
from metagpt.prompts.ml_action import (
    GENERATE_CODE_PROMPT,
    ML_TOOL_USAGE_PROMPT,
    PRINT_DATA_COLUMNS,
    UPDATE_DATA_COLUMNS,
)
from metagpt.prompts.write_analysis_code import CODE_GENERATOR_WITH_TOOLS
from metagpt.schema import Message, Plan
from metagpt.utils.common import create_func_call_config, remove_comments


class WriteCodeWithToolsML(WriteCodeWithTools):
    async def run(
        self,
        context: List[Message],
        plan: Plan = None,
        column_info: str = "",
        **kwargs,
    ) -> Tuple[List[Message], str]:
        # prepare tool schemas and tool-type-specific instruction
        tool_schemas, tool_type_usage_prompt = await self._prepare_tools(plan=plan)

        # ML-specific variables to be used in prompt
        code_steps = plan.current_task.code_steps
        finished_tasks = plan.get_finished_tasks()
        code_context = [remove_comments(task.code) for task in finished_tasks]
        code_context = "\n\n".join(code_context)

        # prepare prompt depending on tool availability & LLM call
        if tool_schemas:
            prompt = ML_TOOL_USAGE_PROMPT.format(
                user_requirement=plan.goal,
                history_code=code_context,
                current_task=plan.current_task.instruction,
                column_info=column_info,
                tool_type_usage_prompt=tool_type_usage_prompt,
                code_steps=code_steps,
                tool_schemas=tool_schemas,
            )

        else:
            prompt = GENERATE_CODE_PROMPT.format(
                user_requirement=plan.goal,
                history_code=code_context,
                current_task=plan.current_task.instruction,
                column_info=column_info,
                tool_type_usage_prompt=tool_type_usage_prompt,
                code_steps=code_steps,
            )
        tool_config = create_func_call_config(CODE_GENERATOR_WITH_TOOLS)
        rsp = await self.llm.aask_code(prompt, **tool_config)

        # Extra output to be used for potential debugging
        context = [Message(content=prompt, role="user")]

        return context, rsp


class UpdateDataColumns(Action):
    async def run(self, plan: Plan = None) -> dict:
        finished_tasks = plan.get_finished_tasks()
        code_context = [remove_comments(task.code) for task in finished_tasks]
        code_context = "\n\n".join(code_context)
        prompt = UPDATE_DATA_COLUMNS.format(history_code=code_context)
        tool_config = create_func_call_config(PRINT_DATA_COLUMNS)
        rsp = await self.llm.aask_code(prompt, **tool_config)
        return rsp
