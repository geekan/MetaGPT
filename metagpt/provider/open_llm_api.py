#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : self-host open llm model with openai-compatible interface

import openai

from metagpt.config import CONFIG, LLMProviderEnum
from metagpt.logs import logger
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.provider.openai_api import CostManager, OpenAIGPTAPI, RateLimiter


class OpenLLMCostManager(CostManager):
    """open llm model is self-host, it's free and without cost"""

    def update_cost(self, prompt_tokens, completion_tokens, model):
        """
        Update the total cost, prompt tokens, and completion tokens.

        Args:
        prompt_tokens (int): The number of tokens used in the prompt.
        completion_tokens (int): The number of tokens used in the completion.
        model (str): The model used for the API call.
        """
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens

        logger.info(
            f"Max budget: ${CONFIG.max_budget:.3f} | "
            f"prompt_tokens: {prompt_tokens}, completion_tokens: {completion_tokens}"
        )
        CONFIG.total_cost = self.total_cost


@register_provider(LLMProviderEnum.OPEN_LLM)
class OpenLLMGPTAPI(OpenAIGPTAPI):
    def __init__(self):
        self.__init_openllm(CONFIG)
        self.llm = openai
        self.model = CONFIG.open_llm_api_model
        self.auto_max_tokens = False
        self._cost_manager = OpenLLMCostManager()
        RateLimiter.__init__(self, rpm=self.rpm)

    def __init_openllm(self, config: "Config"):
        openai.api_key = "sk-xx"  # self-host api doesn't need api-key, use the default value
        openai.api_base = config.open_llm_api_base
        self.rpm = int(config.get("RPM", 10))
