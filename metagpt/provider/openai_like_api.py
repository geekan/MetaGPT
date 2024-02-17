#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : self-host open llm model with openai-compatible interface

from openai.types import CompletionUsage
from openai.types.chat import  ChatCompletionChunk
from metagpt.configs.llm_config import LLMConfig, LLMType
from openai import  AsyncStream
from metagpt.logs import logger,log_llm_stream
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.provider.openai_api import OpenAILLM
from metagpt.utils.cost_manager import Costs, CostManager


@register_provider([LLMType.OPENAI_LIKE,LLMType.OPENAI])
class OpenAILIKE(OpenAILLM):
    """Used for OPENAI-like payment models, unlike OPEN_LLM with added billing functionality"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._cost_manager = CostManager()
        self.model = config.model

    def _make_client_kwargs(self) -> dict:
        kwargs = dict(api_key=self.config.api_key, base_url=self.config.base_url)
        return kwargs

    def _update_costs(self, usage: CompletionUsage):
        if self.config.calc_usage and usage:
            try:
                self._cost_manager.update_cost(usage.prompt_tokens, usage.completion_tokens, self.model)
            except Exception as e:
                logger.error(f"updating costs failed!, exp: {e}")

    def get_costs(self) -> Costs:
        return self._cost_manager.get_costs()

    async def _achat_completion_stream(self, messages: list[dict], timeout=3) -> str:
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
                    log_llm_stream(choice_delta.content)
                if finish_reason:
                    # some services return usage when finish_reason is not None
                    usage = CompletionUsage(**choice.usage)

        log_llm_stream("\n")
        full_content = "".join(collected_content)
        self._update_costs(usage)
        return full_content

    async def acompletion_text(self, messages: list[dict], stream=False, timeout: int = 3) -> str:
        """when streaming, print each token in place."""
        if stream:
            return await self._achat_completion_stream(messages)
        rsp = await self._achat_completion(messages)
        return self.get_choice_text(rsp)
