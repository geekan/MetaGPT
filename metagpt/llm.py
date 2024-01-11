#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:45
@Author  : alexanderwu
@File    : llm.py
"""
from typing import Optional

from metagpt.configs.llm_config import LLMConfig
from metagpt.context import CONTEXT
from metagpt.provider.base_llm import BaseLLM


def LLM(llm_config: Optional[LLMConfig] = None) -> BaseLLM:
    """get the default llm provider if name is None"""
    if llm_config is not None:
        CONTEXT.llm_with_cost_manager_from_llm_config(llm_config)
    return CONTEXT.llm()
