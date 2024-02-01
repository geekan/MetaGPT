import json
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
from metagpt.utils.common import CodeParser, create_func_call_config, remove_comments


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


class Reflect(Action):
    PROMPT_TEMPLATE: str = """
    # Context
    __context__
    # Latest User Requirement
    __user_requirement__
    # Summary
    Above is all your attempts to tackle the user requirement. You plan, act, submit your output, and get the result and feedback.
    Output a json following the format:
    ```json
    {
        "summary": str = "summarize each of your previous trial in a triple of (your methods, the corresponding result, potential improvement), list them out",
        "takeaways": str = "carefully find key takeaways from your summarization",
        "reflection": str = "give specific instruction to improve your next trial in a step-by-step thinking process",
    }
    ```
    """
    REWRITE_PLAN_INSTRUCTION: str = """Take this reflection for rewriting plan, modify the current plan in place, make reference to your specific instruction, think about you should
    change which task, add or delete what tasks in the plan. Only make necessary changes, keep reusable tasks unchanged, output the COMPLETE new plan starting from the first task. Your plan should have no more than 5 tasks."""

    async def run(self, context: str, user_requirement: str = "") -> str:
        user_requirement = user_requirement or "Score as high as possible in a data modeling competition"
        # prompt = self.PROMPT_TEMPLATE.format(context=context, user_requirement=user_requirement)
        prompt = self.PROMPT_TEMPLATE.replace("__context__", context).replace("__user_requirement__", user_requirement)
        rsp_json = await self._aask(prompt)
        rsp = CodeParser.parse_code(block=None, text=rsp_json)
        reflection = json.loads(rsp)["reflection"]
        return reflection


class UpdateDataColumns(Action):
    async def run(self, plan: Plan = None) -> dict:
        finished_tasks = plan.get_finished_tasks()
        code_context = [remove_comments(task.code) for task in finished_tasks]
        code_context = "\n\n".join(code_context)
        prompt = UPDATE_DATA_COLUMNS.format(history_code=code_context)
        tool_config = create_func_call_config(PRINT_DATA_COLUMNS)
        rsp = await self.llm.aask_code(prompt, **tool_config)
        return rsp
