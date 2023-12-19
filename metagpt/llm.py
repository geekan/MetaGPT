#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:45
@Author  : alexanderwu
@File    : llm.py
"""

from metagpt.config import CONFIG, LLMProviderEnum
from metagpt.provider.base_gpt_api import BaseGPTAPI
from metagpt.provider.human_provider import HumanProvider
from metagpt.provider.llm_provider_registry import LLM_REGISTRY

_ = HumanProvider()  # Avoid pre-commit error


def LLM(provider: LLMProviderEnum = CONFIG.get_default_llm_provider_enum()) -> BaseGPTAPI:
    """get the default llm provider"""
    return LLM_REGISTRY.get_provider(provider)
