#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:45
@Author  : alexanderwu
@File    : llm.py
"""

from metagpt.config import CONFIG
from metagpt.provider.anthropic_api import Claude2 as Claude
from metagpt.provider.openai_api import OpenAIGPTAPI
from metagpt.provider.zhipuai_api import ZhiPuAIGPTAPI
from metagpt.provider.spark_api import SparkAPI
from metagpt.provider.open_llm_api import OpenLLMGPTAPI
from metagpt.provider.fireworks_api import FireWorksGPTAPI
from metagpt.provider.human_provider import HumanProvider


def LLM() -> "BaseGPTAPI":
    """ initialize different LLM instance according to the key field existence"""
    # TODO a little trick, can use registry to initialize LLM instance further
    if CONFIG.openai_api_key:
        llm = OpenAIGPTAPI()
    elif CONFIG.claude_api_key:
        llm = Claude()
    elif CONFIG.spark_api_key:
        llm = SparkAPI()
    elif CONFIG.zhipuai_api_key:
        llm = ZhiPuAIGPTAPI()
    elif CONFIG.open_llm_api_base:
        llm = OpenLLMGPTAPI()
    elif CONFIG.fireworks_api_key:
        llm = FireWorksGPTAPI()
    else:
        raise RuntimeError("You should config a LLM configuration first")

    return llm
