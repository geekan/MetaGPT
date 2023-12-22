#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : fireworks.ai's api

import openai

from metagpt.config import CONFIG, LLMProviderEnum
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.provider.openai_api import OpenAIGPTAPI, RateLimiter


@register_provider(LLMProviderEnum.FIREWORKS)
class FireWorksGPTAPI(OpenAIGPTAPI):
    def __init__(self):
        self.__init_fireworks(CONFIG)
        self.llm = openai
        self.model = CONFIG.fireworks_api_model
        self.auto_max_tokens = False
        RateLimiter.__init__(self, rpm=self.rpm)

    def __init_fireworks(self, config: "Config"):
        # TODO: The 'openai.api_base' option isn't read in the client API. You will need to pass it when you
        #  instantiate the client, e.g. 'OpenAI(api_base=config.fireworks_api_base)'
        # openai.api_key = config.fireworks_api_key
        # openai.api_base = config.fireworks_api_base
        self.rpm = int(config.get("RPM", 10))
