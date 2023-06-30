#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:45
@Author  : alexanderwu
@File    : llm.py
"""

from metagpt.provider.openai_api import OpenAIGPTAPI as LLM

DEFAULT_LLM = LLM()


async def ai_func(prompt):
    """使用LLM进行QA"""
    return await DEFAULT_LLM.aask(prompt)
