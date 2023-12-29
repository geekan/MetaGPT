# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/5 23:08
@Author  : alexanderwu
@File    : metagpt_api.py
@Desc    : MetaGPT LLM provider.
"""
from metagpt.config import LLMProviderEnum
from metagpt.provider import OpenAILLM
from metagpt.provider.llm_provider_registry import register_provider


@register_provider(LLMProviderEnum.METAGPT)
class MetaGPTLLM(OpenAILLM):
    def __init__(self):
        super().__init__()
