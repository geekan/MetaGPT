# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/30
@Author  : mashenquan
@File    : metagpt_llm_api.py
@Desc    : MetaGPT LLM related APIs
"""
import json

from pydantic import BaseModel

from metagpt.memory.brain_memory import BrainMemory
from metagpt.provider import OpenAIGPTAPI


class MetaGPTLLMAPI(OpenAIGPTAPI):
    """MetaGPT LLM api"""

    def __init__(self):
        super().__init__()

    async def get_summary(self, memory: BrainMemory, max_words=200, keep_language: bool = False, **kwargs):
        summary = []

        class QuweryAnswerPair(BaseModel):
            ask: str
            answer: str

        rh = reversed(memory.history)
        ix = 0
        while ix < len(rh):
            t = rh[ix]
            print(t)
            # 如果 t是ask, continue
            pass

        data = json.dumps(summary)
        return data
