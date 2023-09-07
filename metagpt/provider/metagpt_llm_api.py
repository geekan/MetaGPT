# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/30
@Author  : mashenquan
@File    : metagpt_llm_api.py
@Desc    : MetaGPT LLM related APIs
"""
import json
from typing import Dict, List

from pydantic import BaseModel

from metagpt.memory.brain_memory import MessageType
from metagpt.provider import OpenAIGPTAPI


class HisMsg(BaseModel):
    content: str
    tags: set
    id: str


class Conversion(BaseModel):
    """See: https://github.com/openai/openai-cookbook/blob/main/examples/How_to_format_inputs_to_ChatGPT_models.ipynb"""

    role: str
    content: str


class MetaGPTLLMAPI(OpenAIGPTAPI):
    """MetaGPT LLM api"""

    def __init__(self):
        super().__init__()

    async def get_summary(self, history: List[Dict], max_words=200, keep_language: bool = False, **kwargs) -> str:
        """
        Return string in the following format：
        [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Knock knock."},
            {"role": "assistant", "content": "Who's there?"},
            {"role": "user", "content": "Orange."},
        ]
        """
        summary = []

        total_length = 0
        for m in reversed(history):
            msg = HisMsg(**m)
            c = Conversion(role="user" if MessageType.Talk.value in msg.tags else "assistant", content=msg.content)
            length_delta = len(msg.content)
            if total_length + length_delta > max_words:
                left = max_words - total_length
                if left > 0:
                    c.content = msg.content[0:left]
                    summary.insert(0, c.dict())
                break

            total_length += length_delta
            summary.insert(0, c.dict())

        data = json.dumps(summary)
        return data
