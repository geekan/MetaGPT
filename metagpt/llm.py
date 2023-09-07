#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:45
@Author  : alexanderwu
@File    : llm.py
@Modified By: mashenquan, 2023
"""
from enum import Enum

from metagpt.config import CONFIG
from metagpt.provider.anthropic_api import Claude2 as Claude
from metagpt.provider.metagpt_llm_api import MetaGPTLLMAPI as MetaGPT_LLM
from metagpt.provider.openai_api import OpenAIGPTAPI as OpenAI_LLM


class LLMType(Enum):
    OPENAI = "OpenAI"
    METAGPT = "MetaGPT"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def get(cls, value):
        for member in cls:
            if member.value == value:
                return member
        return cls.UNKNOWN


DEFAULT_LLM = OpenAI_LLM()
DEFAULT_METAGPT_LLM = MetaGPT_LLM()
CLAUDE_LLM = Claude()


async def ai_func(prompt):
    """使用LLM进行QA
    QA with LLMs
    """
    return await DEFAULT_LLM.aask(prompt)


class LLMFactory:
    @staticmethod
    async def new_llm() -> object:
        llm = OpenAI_LLM() if CONFIG.LLM_TYPE == LLMType.OPENAI.value else MetaGPT_LLM()
        return llm
