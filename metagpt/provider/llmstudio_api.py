# -*- coding: utf-8 -*-
"""
@Time    : 2025/2/10 10:00
@Author  : terrdi
@File    : llmstudio_api.py
@Desc    : LLMStudio LLM provider.
"""
from metagpt.configs.llm_config import LLMType
from metagpt.provider import OpenAILLM
from metagpt.provider.llm_provider_registry import register_provider


@register_provider(LLMType.LLMSTUDIO)
class LLMStudioLLM(OpenAILLM):
    pass
