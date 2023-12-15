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
from metagpt.provider.base_gpt_api import BaseGPTAPI
from metagpt.provider.fireworks_api import FireWorksGPTAPI
from metagpt.provider.human_provider import HumanProvider
from metagpt.provider.metagpt_llm_api import MetaGPTLLMAPI
from metagpt.provider.open_llm_api import OpenLLMGPTAPI
from metagpt.provider.openai_api import OpenAIGPTAPI
from metagpt.provider.spark_api import SparkAPI
from metagpt.provider.zhipuai_api import ZhiPuAIGPTAPI

_ = HumanProvider()  # Avoid pre-commit error


# Used in agents
class LLMFactory:
    @staticmethod
    def new_llm() -> "BaseGPTAPI":
        # Determine which type of LLM to use based on the validity of the key.
        if CONFIG.spark_api_key:
            return SparkAPI()
        elif CONFIG.zhipuai_api_key:
            return ZhiPuAIGPTAPI()
        elif CONFIG.open_llm_api_base:
            return OpenLLMGPTAPI()
        elif CONFIG.fireworks_api_key:
            return FireWorksGPTAPI()

        # MetaGPT uses the same parameters as OpenAI.
        constructors = {
            LLMType.OPENAI.value: OpenAIGPTAPI,
            LLMType.METAGPT.value: MetaGPTLLMAPI,
        }
        constructor = constructors.get(CONFIG.LLM_TYPE)
        if constructor:
            return constructor()

        raise RuntimeError("You should config a LLM configuration first")


# Used in metagpt
def LLM() -> "BaseGPTAPI":
    """initialize different LLM instance according to the key field existence"""
    return LLMFactory.new_llm()
