#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:45
@Author  : alexanderwu
@File    : llm.py
"""

from typing import Optional

from metagpt.config import CONFIG, LLMProviderEnum
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.human_provider import HumanProvider
from metagpt.provider.llm_provider_registry import LLM_REGISTRY

_ = HumanProvider()  # Avoid pre-commit error


def LLM(provider: Optional[LLMProviderEnum] = None) -> BaseLLM:
    """get the default llm provider"""
    if provider is None:
        provider = CONFIG.get_default_llm_provider_enum()

    return LLM_REGISTRY.get_provider(provider)
