#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : fireworks.ai's api

import re

from openai import APIConnectionError, AsyncStream
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletionChunk
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.logs import logger
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.provider.openai_api import OpenAILLM, log_and_reraise
from metagpt.utils.cost_manager import CostManager, Costs

MODEL_GRADE_TOKEN_COSTS = {
    "-1": {"prompt": 0.0, "completion": 0.0},  # abnormal condition
    "16": {"prompt": 0.2, "completion": 0.8},  # 16 means model size <= 16B; 0.2 means $0.2/1M tokens
    "80": {"prompt": 0.7, "completion": 2.8},  # 80 means 16B < model size <= 80B
    "mixtral-8x7b": {"prompt": 0.4, "completion": 1.6},
}


class FireworksCostManager(CostManager):
    """Manages the costs associated with using different model grades for token generation.

    This class extends the CostManager to specifically handle the cost calculation based on
    the model grade and token usage for the Fireworks LLM provider.
    """

    def model_grade_token_costs(self, model: str) -> dict[str, float]:
        """Calculates the token costs based on the model grade.

        Args:
            model: The model grade as a string.

        Returns:
            A dictionary with 'prompt' and 'completion' costs.
        """

        def _get_model_size(model: str) -> float:
            size = re.findall(".*-([0-9.]+)b", model)
            size = float(size[0]) if len(size) > 0 else -1
            return size

        if "mixtral-8x7b" in model:
            token_costs = MODEL_GRADE_TOKEN_COSTS["mixtral-8x7b"]
        else:
            model_size = _get_model_size(model)
            if 0 < model_size <= 16:
                token_costs = MODEL_GRADE_TOKEN_COSTS["16"]
            elif 16 < model_size <= 80:
                token_costs = MODEL_GRADE_TOKEN_COSTS["80"]
            else:
                token_costs = MODEL_GRADE_TOKEN_COSTS["-1"]
        return token_costs

    def update_cost(self, prompt_tokens: int, completion_tokens: int, model: str):
        """Updates the total cost, prompt tokens, and completion tokens based on usage.

        Args:
            prompt_tokens: The number of tokens used in the prompt.
            completion_tokens: The number of tokens used in the completion.
            model: The model used for the API call.
        """
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens

        token_costs = self.model_grade_token_costs(model)
        cost = (prompt_tokens * token_costs["prompt"] + completion_tokens * token_costs["completion"]) / 1000000
        self.total_cost += cost
        logger.info(
            f"Total running cost: ${self.total_cost:.4f}"
            f"Current cost: ${cost:.4f}, prompt_tokens: {prompt_tokens}, completion_tokens: {completion_tokens}"
        )


@register_provider(LLMType.FIREWORKS)
class FireworksLLM(OpenAILLM):
    """Provides an interface to the Fireworks LLM, extending OpenAILLM.

    This class is responsible for managing interactions with the Fireworks LLM, including
    cost management and API calls.
    """

    def __init__(self, config: LLMConfig):
        """Initializes the FireworksLLM with a given configuration.

        Args:
            config: The configuration settings for the LLM.
        """
        super().__init__(config=config)
        self.auto_max_tokens = False
        self.cost_manager = FireworksCostManager()

    def _make_client_kwargs(self) -> dict:
        """Prepares the keyword arguments for the API client based on the configuration.

        Returns:
            A dictionary of API client keyword arguments.
        """
        kwargs = dict(api_key=self.config.api_key, base_url=self.config.base_url)
        return kwargs

    def _update_costs(self, usage: CompletionUsage):
        """Updates the cost manager with the usage information.

        Args:
            usage: The usage information from a completion operation.
        """
        if self.config.calc_usage and usage:
            try:
                # use FireworksCostManager not context.cost_manager
                self.cost_manager.update_cost(usage.prompt_tokens, usage.completion_tokens, self.model)
            except Exception as e:
                logger.error(f"updating costs failed!, exp: {e}")

    def get_costs(self) -> Costs:
        """Retrieves the current costs from the cost manager.

        Returns:
            An instance of Costs containing the current cost information.
        """
        return self.cost_manager.get_costs()

    async def _achat_completion_stream(self, messages: list[dict], timeout=3) -> str:
        """Handles asynchronous chat completion stream requests.

        Args:
            messages: A list of message dictionaries to be sent.
            timeout: The timeout value for the request.

        Returns:
            The full content collected from the stream response.
        """
        response: AsyncStream[ChatCompletionChunk] = await self.aclient.chat.completions.create(
            **self._cons_kwargs(messages), stream=True
        )

        collected_content = []
        usage = CompletionUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        # iterate through the stream of events
        async for chunk in response:
            if chunk.choices:
                choice = chunk.choices[0]
                choice_delta = choice.delta
                finish_reason = choice.finish_reason if hasattr(choice, "finish_reason") else None
                if choice_delta.content:
                    collected_content.append(choice_delta.content)
                    print(choice_delta.content, end="")
                if finish_reason:
                    # fireworks api return usage when finish_reason is not None
                    usage = CompletionUsage(**chunk.usage)

        full_content = "".join(collected_content)
        self._update_costs(usage)
        return full_content

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
        after=after_log(logger, logger.level("WARNING").name),
        retry=retry_if_exception_type(APIConnectionError),
        retry_error_callback=log_and_reraise,
    )
    async def acompletion_text(self, messages: list[dict], stream=False, timeout: int = 3) -> str:
        """Performs an asynchronous completion text operation.

        Args:
            messages: A list of message dictionaries for the completion request.
            stream: Whether to stream the response.
            timeout: The timeout value for the request.

        Returns:
            The text result from the completion operation.
        """
        if stream:
            return await self._achat_completion_stream(messages)
        rsp = await self._achat_completion(messages)
        return self.get_choice_text(rsp)
