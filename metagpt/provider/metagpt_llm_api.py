# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/30
@Author  : mashenquan
@File    : metagpt_llm_api.py
@Desc    : MetaGPT LLM related APIs
"""

from metagpt.provider import OpenAIGPTAPI


class MetaGPTLLMAPI(OpenAIGPTAPI):
    """MetaGPT LLM api"""

    def __init__(self):
        super().__init__()

    async def get_summary(self, memory, max_words=200, keep_language: bool = False, **kwargs) -> str:
        """
        Return string in the following format：
        [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Knock knock."},
            {"role": "assistant", "content": "Who's there?"},
            {"role": "user", "content": "Orange."},
        ]
        """
        return memory.dumps_raw_messages(max_length=max_words)
