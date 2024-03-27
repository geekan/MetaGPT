# -*- encoding: utf-8 -*-
"""
@Date    :   2023/11/20 13:19:39
@Author  :   orange-crow
@File    :   write_analysis_code.py
"""
from __future__ import annotations

import json

from metagpt.actions import Action
from metagpt.prompts.di.write_analysis_code import (
    CHECK_DATA_PROMPT,
    DEBUG_REFLECTION_EXAMPLE,
    INTERPRETER_SYSTEM_MSG,
    REFLECTION_PROMPT,
    REFLECTION_SYSTEM_MSG,
    STRUCTUAL_PROMPT,
)
from metagpt.schema import Message, Plan
from metagpt.utils.common import CodeParser, remove_comments


class WriteAnalysisCode(Action):
    async def _debug_with_reflection(self, context: list[Message], working_memory: list[Message]):
        reflection_prompt = REFLECTION_PROMPT.format(
            debug_example=DEBUG_REFLECTION_EXAMPLE,
            context=context,
            previous_impl=working_memory,
        )

        rsp = await self._aask(reflection_prompt, system_msgs=[REFLECTION_SYSTEM_MSG])
        reflection = json.loads(CodeParser.parse_code(block=None, text=rsp))

        return reflection["improved_impl"]

    async def run(
        self,
        user_requirement: str,
        plan_status: str = "",
        tool_info: str = "",
        working_memory: list[Message] = None,
        use_reflection: bool = False,
        **kwargs,
    ) -> str:
        structual_prompt = STRUCTUAL_PROMPT.format(
            user_requirement=user_requirement,
            plan_status=plan_status,
            tool_info=tool_info,
        )

        working_memory = working_memory or []
        context = self.llm.format_msg([Message(content=structual_prompt, role="user")] + working_memory)

        # LLM call
        if use_reflection:
            code = await self._debug_with_reflection(context=context, working_memory=working_memory)
        else:
            rsp = await self.llm.aask(context, system_msgs=[INTERPRETER_SYSTEM_MSG], **kwargs)
            code = CodeParser.parse_code(block=None, text=rsp)

        return code


class CheckData(Action):
    async def run(self, plan: Plan) -> dict:
        finished_tasks = plan.get_finished_tasks()
        code_written = [remove_comments(task.code) for task in finished_tasks]
        code_written = "\n\n".join(code_written)
        prompt = CHECK_DATA_PROMPT.format(code_written=code_written)
        rsp = await self._aask(prompt)
        code = CodeParser.parse_code(block=None, text=rsp)
        return code
