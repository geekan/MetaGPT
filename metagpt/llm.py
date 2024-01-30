#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/5/11 14:45
# @Author  : alexanderwu
# @File    : llm.py

from typing import Optional

from metagpt.configs.llm_config import LLMConfig
from metagpt.context import Context
from metagpt.provider.base_llm import BaseLLM


def LLM(llm_config: Optional[LLMConfig] = None, context: Context = None) -> BaseLLM:
    """Get the default LLM provider if name is None.

    Args:
        llm_config: Optional configuration for the LLM. If provided, it configures the LLM with specific settings.
        context: The context in which the LLM operates. If not provided, a default context is used.

    Returns:
        An instance of BaseLLM configured according to the provided LLMConfig and Context.
    """
    ctx = context or Context()
    if llm_config is not None:
        ctx.llm_with_cost_manager_from_llm_config(llm_config)
    return ctx.llm()
