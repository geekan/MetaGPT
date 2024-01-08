#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:45
@Author  : alexanderwu
@File    : llm.py
"""

from typing import Optional

from metagpt.configs.llm_config import LLMType
from metagpt.context import context
from metagpt.provider.base_llm import BaseLLM


def LLM(name: Optional[str] = None, provider: LLMType = LLMType.OPENAI) -> BaseLLM:
    """get the default llm provider if name is None"""
    return context.llm(name=name, provider=provider)
