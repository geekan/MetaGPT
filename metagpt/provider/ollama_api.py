#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : self-host open llm model with ollama which isn't openai-api-compatible

import json

from requests import ConnectionError
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from metagpt.config import CONFIG, LLMProviderEnum
from metagpt.const import LLM_API_TIMEOUT
from metagpt.logs import log_llm_stream, logger
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.general_api_requestor import GeneralAPIRequestor
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.provider.openai_api import log_and_reraise
from metagpt.utils.cost_manager import CostManager


class OllamaCostManager(CostManager):
    def update_cost(self, prompt_tokens, completion_tokens, model):
        """
        Update the total cost, prompt tokens, and completion tokens.
        """
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        max_budget = CONFIG.max_budget if CONFIG.max_budget else CONFIG.cost_manager.max_budget
        logger.info(
            f"Max budget: ${max_budget:.3f} | "
            f"prompt_tokens: {prompt_tokens}, completion_tokens: {completion_tokens}"
        )
        CONFIG.total_cost = self.total_cost


@register_provider(LLMProviderEnum.OLLAMA)
class OllamaLLM(BaseLLM):
    """
    Refs to `https://github.com/jmorganca/ollama/blob/main/docs/api.md#generate-a-chat-completion`
    """

    def __init__(self):
        self.__init_ollama(CONFIG)
        self.client = GeneralAPIRequestor(base_url=CONFIG.ollama_api_base)
        self.suffix_url = "/chat"
        self.http_method = "post"
        self.use_system_prompt = False
        self._cost_manager = OllamaCostManager()

    def __init_ollama(self, config: CONFIG):
        assert config.ollama_api_base
        self.model = config.ollama_api_model

    def _const_kwargs(self, messages: list[dict], stream: bool = False) -> dict:
        kwargs = {"model": self.model, "messages": messages, "options": {"temperature": 0.3}, "stream": stream}
        return kwargs

    def _update_costs(self, usage: dict):
        """update each request's token cost"""
        if CONFIG.calc_usage:
            try:
                prompt_tokens = int(usage.get("prompt_tokens", 0))
                completion_tokens = int(usage.get("completion_tokens", 0))
                self._cost_manager.update_cost(prompt_tokens, completion_tokens, self.model)
            except Exception as e:
                logger.error(f"ollama updats costs failed! exp: {e}")

    def get_choice_text(self, resp: dict) -> str:
        """get the resp content from llm response"""
        assist_msg = resp.get("message", {})
        assert assist_msg.get("role", None) == "assistant"
        return assist_msg.get("content")

    def get_usage(self, resp: dict) -> dict:
        return {"prompt_tokens": resp.get("prompt_eval_count", 0), "completion_tokens": resp.get("eval_count", 0)}

    def _decode_and_load(self, chunk: bytes, encoding: str = "utf-8") -> dict:
        chunk = chunk.decode(encoding)
        return json.loads(chunk)

    async def _achat_completion(self, messages: list[dict]) -> dict:
        resp, _, _ = await self.client.arequest(
            method=self.http_method,
            url=self.suffix_url,
            params=self._const_kwargs(messages),
            request_timeout=LLM_API_TIMEOUT,
        )
        resp = self._decode_and_load(resp)
        usage = self.get_usage(resp)
        self._update_costs(usage)
        return resp

    async def acompletion(self, messages: list[dict], timeout=3) -> dict:
        return await self._achat_completion(messages)

    async def _achat_completion_stream(self, messages: list[dict]) -> str:
        stream_resp, _, _ = await self.client.arequest(
            method=self.http_method,
            url=self.suffix_url,
            stream=True,
            params=self._const_kwargs(messages, stream=True),
            request_timeout=LLM_API_TIMEOUT,
        )

        collected_content = []
        usage = {}
        async for raw_chunk in stream_resp:
            chunk = self._decode_and_load(raw_chunk)

            if not chunk.get("done", False):
                content = self.get_choice_text(chunk)
                collected_content.append(content)
                log_llm_stream(content)
            else:
                # stream finished
                usage = self.get_usage(chunk)

        self._update_costs(usage)
        full_content = "".join(collected_content)
        return full_content

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_random_exponential(min=1, max=60),
        after=after_log(logger, logger.level("WARNING").name),
        retry=retry_if_exception_type(ConnectionError),
        retry_error_callback=log_and_reraise,
    )
    async def acompletion_text(self, messages: list[dict], stream=False, timeout: int = 3) -> str:
        """response in async with stream or non-stream mode"""
        if stream:
            return await self._achat_completion_stream(messages)
        resp = await self._achat_completion(messages)
        return self.get_choice_text(resp)
