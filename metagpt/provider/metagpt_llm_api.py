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
