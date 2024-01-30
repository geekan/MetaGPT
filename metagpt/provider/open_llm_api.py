#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : self-host open llm model with openai-compatible interface

from openai.types import CompletionUsage

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.logs import logger
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.provider.openai_api import OpenAILLM
from metagpt.utils.cost_manager import Costs, TokenCostManager
from metagpt.utils.token_counter import count_message_tokens, count_string_tokens


@register_provider(LLMType.OPEN_LLM)
class OpenLLM(OpenAILLM):
    """A class for managing interactions with OpenAI's LLM.

    This class extends the OpenAILLM class to provide specific functionalities
    for OpenAI's language models, including cost management and usage calculation.

    Args:
        config: Configuration settings for the language model.

    Attributes:
        _cost_manager: Manages the token costs associated with using the model.
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._cost_manager = TokenCostManager()

    def _make_client_kwargs(self) -> dict:
        """Creates the keyword arguments required for the OpenAI client.

        Returns:
            A dictionary of client keyword arguments.
        """
        kwargs = dict(api_key="sk-xxx", base_url=self.config.base_url)
        return kwargs

    def _calc_usage(self, messages: list[dict], rsp: str) -> CompletionUsage:
        """Calculates the token usage for a given request and response.

        Args:
            messages: A list of dictionaries representing the input messages.
            rsp: The response string from the model.

        Returns:
            An instance of CompletionUsage detailing the token usage.
        """
        usage = CompletionUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        if not self.config.calc_usage:
            return usage

        try:
            usage.prompt_tokens = count_message_tokens(messages, "open-llm-model")
            usage.completion_tokens = count_string_tokens(rsp, "open-llm-model")
        except Exception as e:
            logger.error(f"usage calculation failed!: {e}")

        return usage

    def _update_costs(self, usage: CompletionUsage):
        """Updates the cost manager with the token usage of a request.

        Args:
            usage: An instance of CompletionUsage detailing the token usage.
        """
        if self.config.calc_usage and usage:
            try:
                # use OpenLLMCostManager not CONFIG.cost_manager
                self._cost_manager.update_cost(usage.prompt_tokens, usage.completion_tokens, self.model)
            except Exception as e:
                logger.error(f"updating costs failed!, exp: {e}")

    def get_costs(self) -> Costs:
        """Retrieves the current costs from the cost manager.

        Returns:
            An instance of Costs detailing the current costs.
        """
        return self._cost_manager.get_costs()
