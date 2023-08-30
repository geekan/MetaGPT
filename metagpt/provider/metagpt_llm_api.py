# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/30
@Author  : mashenquan
@File    : metagpt_llm_api.py
@Desc    : MetaGPT LLM related APIs
"""

import openai

from metagpt.config import CONFIG
from metagpt.provider import OpenAIGPTAPI
from metagpt.provider.openai_api import RateLimiter


class MetaGPTLLMAPI(OpenAIGPTAPI):
    """MetaGPT LLM api"""

    def __init__(self):
        self.__init_openai()
        self.llm = openai
        self.model = CONFIG.METAGPT_API_MODEL
        self.auto_max_tokens = False
        RateLimiter.__init__(self, rpm=self.rpm)

    def __init_openai(self):
        openai.api_key = CONFIG.METAGPT_API_KEY
        if CONFIG.METAGPT_API_BASE:
            openai.api_base = CONFIG.METAGPT_API_BASE
        if CONFIG.METAGPT_API_TYPE:
            openai.api_type = CONFIG.METAGPT_API_TYPE
            openai.api_version = CONFIG.METAGPT_API_VERSION
        self.rpm = int(CONFIG.RPM) if CONFIG.RPM else 10
