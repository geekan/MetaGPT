#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:45
@Author  : alexanderwu
@File    : llm.py
@Modified By: mashenquan, 2023
@Modified By: mashenquan, 2023-11-7. Update openai to v1.0.0.
"""
from enum import Enum

from metagpt.config import CONFIG


class LLMType(Enum):
    OPENAI = "OpenAI"
    METAGPT = "MetaGPT"
    CLAUDE = "Claude"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def get(cls, value):
        for member in cls:
            if member.value == value:
                return member
        return cls.UNKNOWN


class LLMFactory:
    @staticmethod
    def new_llm() -> object:
        from metagpt.provider.anthropic_api import Claude2 as Claude
        from metagpt.provider.metagpt_llm_api import MetaGPTLLMAPI as MetaGPT_LLM
        from metagpt.provider.openai_api import OpenAIGPTAPI as OpenAI_LLM

        if CONFIG.LLM_TYPE == LLMType.OPENAI.value:
            return OpenAI_LLM()
        if CONFIG.LLM_TYPE == LLMType.METAGPT.value:
            return MetaGPT_LLM()
        if CONFIG.LLM_TYPE == LLMType.CLAUDE.value:
            return Claude()

        raise TypeError(f"Unsupported LLM TYPE: {CONFIG.LLM_TYPE}")
