#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

import json

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.logs import log_llm_stream
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.general_api_requestor import GeneralAPIRequestor, OpenAIResponse
from metagpt.provider.llm_provider_registry import register_provider


@register_provider([LLMType.OPENROUTER_REASONING])
class OpenrouterReasoningLLM(BaseLLM):
    def __init__(self, config: LLMConfig):
        self.client = GeneralAPIRequestor(base_url=config.base_url)
        self.config = config
        self.model = self.config.model
        self.http_method = "post"
        self.base_url = "https://openrouter.ai/api/v1"
        self.url_suffix = "/chat/completions"
        self.headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.config.api_key}"}

    def decode(self, response: OpenAIResponse) -> dict:
        return json.loads(response.data.decode("utf-8"))

    def _const_kwargs(
        self, messages: list[dict], stream: bool = False, timeout=USE_CONFIG_TIMEOUT, **extra_kwargs
    ) -> dict:
        kwargs = {
            "messages": messages,
            "include_reasoning": True,
            "max_tokens": self.config.max_token,
            "temperature": self.config.temperature,
            "model": self.model,
            "stream": stream,
        }
        return kwargs

    def get_choice_text(self, rsp: dict) -> str:
        if "reasoning" in rsp["choices"][0]["message"]:
            self.reasoning_content = rsp["choices"][0]["message"]["reasoning"]
        return rsp["choices"][0]["message"]["content"]

    async def _achat_completion(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> dict:
        payload = self._const_kwargs(messages)
        resp, _, _ = await self.client.arequest(
            url=self.url_suffix, method=self.http_method, params=payload, headers=self.headers  # empty
        )
        resp = resp.decode_asjson()
        self._update_costs(resp["usage"], model=self.model)
        return resp

    async def acompletion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> dict:
        return await self._achat_completion(messages, timeout=self.get_timeout(timeout))

    async def _achat_completion_stream(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> str:
        self.headers["Content-Type"] = "text/event-stream"  # update header to adapt the client
        payload = self._const_kwargs(messages, stream=True)
        resp, _, _ = await self.client.arequest(
            url=self.url_suffix, method=self.http_method, params=payload, headers=self.headers, stream=True  # empty
        )
        collected_content = []
        collected_reasoning_content = []
        usage = {}
        async for chunk in resp:
            chunk = chunk.decode_asjson()
            if not chunk:
                continue
            delta = chunk["choices"][0]["delta"]
            if "reasoning" in delta and delta["reasoning"]:
                collected_reasoning_content.append(delta["reasoning"])
            elif delta["content"]:
                collected_content.append(delta["content"])
                log_llm_stream(delta["content"])

            usage = chunk.get("usage")

        log_llm_stream("\n")
        self._update_costs(usage, model=self.model)
        full_content = "".join(collected_content)
        if collected_reasoning_content:
            self.reasoning_content = "".join(collected_reasoning_content)
        return full_content
