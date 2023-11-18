#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:45
@Author  : alexanderwu
@File    : llm.py
"""

from metagpt.provider.anthropic_api import Claude2 as Claude
from metagpt.provider.openai_api import OpenAIGPTAPI as LLM
from metagpt.provider.human_provider import HumanProvider

DEFAULT_LLM = LLM()
CLAUDE_LLM = Claude()

async def ai_func(prompt):
    """使用LLM进行QA
       QA with LLMs
     """
    return await DEFAULT_LLM.aask(prompt)
