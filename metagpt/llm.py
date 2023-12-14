#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:45
@Author  : alexanderwu
@File    : llm.py
@Modified By: mashenquan, 2023
"""

from metagpt.config import CONFIG
from metagpt.provider import LLMType
from metagpt.provider.anthropic_api import Claude2 as Claude
from metagpt.provider.human_provider import HumanProvider
from metagpt.provider.metagpt_llm_api import MetaGPTLLMAPI
from metagpt.provider.openai_api import OpenAIGPTAPI
from metagpt.provider.spark_api import SparkAPI
from metagpt.provider.zhipuai_api import ZhiPuAIGPTAPI

_ = HumanProvider()  # Avoid pre-commit error


# Used in agents
class LLMFactory:
    @staticmethod
    def new_llm() -> "BaseGPTAPI":
        # Determine which type of LLM to use based on the validity of the key.
        if CONFIG.claude_api_key:
            return Claude()
        elif CONFIG.spark_api_key:
            return SparkAPI()
        elif CONFIG.zhipuai_api_key:
            return ZhiPuAIGPTAPI()

        # MetaGPT uses the same parameters as OpenAI.
        constructors = {
            LLMType.OPENAI.value: OpenAIGPTAPI,
            LLMType.METAGPT.value: MetaGPTLLMAPI,
        }
        constructor = constructors.get(CONFIG.LLM_TYPE)
        if constructor:
            return constructor()

        raise ValueError(f"Unsupported LLM TYPE: {CONFIG.LLM_TYPE}")


# Used in metagpt
def LLM() -> "BaseGPTAPI":
    """initialize different LLM instance according to the key field existence"""
    return LLMFactory.new_llm()
