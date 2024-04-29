# -*- encoding: utf-8 -*-
"""
@Date    :   2023/11/20 13:19:39
@Author  :   orange-crow
@File    :   write_analysis_code.py
"""
from __future__ import annotations

from typing import Union

from metagpt.actions import Action
from metagpt.schema import Message

STRUCTUAL_PROMPT = """
# User Requirement
{user_requirement}

# Plan Status
{plan_status}

# Tool Info
{tool_info}

# Reference Information
{info}
# Constraints
- Take on Current Task if it is in Plan Status, otherwise, tackle User Requirement directly.
"""


class WriteAnalysisReport(Action):
    async def run(
        self,
        user_requirement: str,
        plan_status: str = "",
        tool_info: str = "",
        working_memory: list[Message] = None,
        use_reflection: bool = False,
        **kwargs,
    ) -> str:
        info = "\n".join([str(ct) for ct in working_memory]) if working_memory else ""

        structual_prompt = STRUCTUAL_PROMPT.format(
            user_requirement=user_requirement, plan_status=plan_status, tool_info=tool_info, info=info
        )
        context = self.process_message([Message(content=structual_prompt, role="user")])
        rsp = await self.llm.aask(context, **kwargs)
        return rsp

    def process_message(self, messages: Union[str, Message, list[dict], list[Message], list[str]]) -> list[dict]:
        """convert messages to list[dict]."""
        from metagpt.schema import Message

        # 全部转成list
        if not isinstance(messages, list):
            messages = [messages]

        # 转成list[dict]
        processed_messages = []
        for msg in messages:
            if isinstance(msg, str):
                processed_messages.append({"role": "user", "content": msg})
            elif isinstance(msg, dict):
                assert set(msg.keys()) == set(["role", "content"])
                processed_messages.append(msg)
            elif isinstance(msg, Message):
                processed_messages.append(msg.to_dict())
            else:
                raise ValueError(
                    f"Only support message type are: str, Message, dict, but got {type(messages).__name__}!"
                )
        return processed_messages
