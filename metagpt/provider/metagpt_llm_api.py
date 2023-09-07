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

from metagpt.provider import OpenAIGPTAPI


class MetaGPTLLMAPI(OpenAIGPTAPI):
    """MetaGPT LLM api"""

    def __init__(self):
        super().__init__()

    async def get_summary(self, history: List[Dict], max_words=200, keep_language: bool = False, **kwargs):
        summary = []

        class HisMsg(BaseModel):
            content: str
            tags: set
            id: str

        class QuweryAnswerPair(BaseModel):
            ask: str
            answer: str

        rh = reversed(history)
        ix = 0
        while ix < len(rh):
            t = HisMsg(**rh[ix])
            print(t)
            # 如果 t是ask, continue
            pass

        data = json.dumps(summary)
        return data
