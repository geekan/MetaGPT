#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : fireworks.ai's api

import openai

from metagpt.config import CONFIG
from metagpt.provider.openai_api import OpenAIGPTAPI, RateLimiter
from metagpt.utils.cost_manager import CostManager


class FireWorksGPTAPI(OpenAIGPTAPI):
    def __init__(self):
        self.__init_fireworks(CONFIG)
        self.llm = openai
        self.model = CONFIG.fireworks_api_model
        self.auto_max_tokens = False
        self._cost_manager = CostManager()
        RateLimiter.__init__(self, rpm=self.rpm)

    def __init_fireworks(self, config: "Config"):
        openai.api_key = config.fireworks_api_key
        openai.api_base = config.fireworks_api_base
        self.rpm = int(config.get("RPM", 10))
