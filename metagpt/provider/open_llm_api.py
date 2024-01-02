#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : self-host open llm model with openai-compatible interface

from openai.types import CompletionUsage

from metagpt.config import CONFIG, Config, LLMProviderEnum
from metagpt.logs import logger
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.provider.openai_api import OpenAILLM
from metagpt.utils.cost_manager import CostManager, Costs
from metagpt.utils.token_counter import count_message_tokens, count_string_tokens


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
        max_budget = CONFIG.max_budget if CONFIG.max_budget else CONFIG.cost_manager.max_budget
        logger.info(
            f"Max budget: ${max_budget:.3f} | reference "
            f"prompt_tokens: {prompt_tokens}, completion_tokens: {completion_tokens}"
        )


@register_provider(LLMProviderEnum.OPEN_LLM)
class OpenLLM(OpenAILLM):
    def __init__(self):
        self.config: Config = CONFIG
        self.__init_openllm()
        self.auto_max_tokens = False
        self._cost_manager = OpenLLMCostManager()

    def __init_openllm(self):
        self.is_azure = False
        self.rpm = int(self.config.get("RPM", 10))
        self._init_client()
        self.model = self.config.open_llm_api_model  # `self.model` should after `_make_client` to rewrite it

    def _make_client_kwargs(self) -> dict:
        kwargs = dict(api_key="sk-xxx", base_url=self.config.open_llm_api_base)
        return kwargs

    def _calc_usage(self, messages: list[dict], rsp: str) -> CompletionUsage:
        usage = CompletionUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        if not CONFIG.calc_usage:
            return usage

        try:
            usage.prompt_tokens = count_message_tokens(messages, "open-llm-model")
            usage.completion_tokens = count_string_tokens(rsp, "open-llm-model")
        except Exception as e:
            logger.error(f"usage calculation failed!: {e}")

        return usage

    def _update_costs(self, usage: CompletionUsage):
        if self.config.calc_usage and usage:
            try:
                # use OpenLLMCostManager not CONFIG.cost_manager
                self._cost_manager.update_cost(usage.prompt_tokens, usage.completion_tokens, self.model)
            except Exception as e:
                logger.error(f"updating costs failed!, exp: {e}")

    def get_costs(self) -> Costs:
        return self._cost_manager.get_costs()
