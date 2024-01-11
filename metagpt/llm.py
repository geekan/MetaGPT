#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:45
@Author  : alexanderwu
@File    : llm.py
"""


from metagpt.context import CONTEXT
from metagpt.provider.base_llm import BaseLLM


def LLM() -> BaseLLM:
    """get the default llm provider if name is None"""
    # context.use_llm(name=name, provider=provider)
    return CONTEXT.llm()
