#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : Google Gemini LLM from https://ai.google.dev/tutorials/python_quickstart

from typing import Optional, Union

import google.generativeai as genai
from google.ai import generativelanguage as glm
from google.generativeai.generative_models import GenerativeModel
from google.generativeai.types import content_types
from google.generativeai.types.generation_types import (
    AsyncGenerateContentResponse,
    GenerateContentResponse,
    GenerationConfig,
)

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.logs import log_llm_stream
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.llm_provider_registry import register_provider


class GeminiGenerativeModel(GenerativeModel):
    """
    Due to `https://github.com/google/generative-ai-python/pull/123`, inherit a new class.
    Will use default GenerativeModel if it fixed.
    """

    def count_tokens(self, contents: content_types.ContentsType) -> glm.CountTokensResponse:
        contents = content_types.to_contents(contents)
        return self._client.count_tokens(model=self.model_name, contents=contents)

    async def count_tokens_async(self, contents: content_types.ContentsType) -> glm.CountTokensResponse:
        contents = content_types.to_contents(contents)
        return await self._async_client.count_tokens(model=self.model_name, contents=contents)


@register_provider(LLMType.GEMINI)
class GeminiLLM(BaseLLM):
    """
    Refs to `https://ai.google.dev/tutorials/python_quickstart`
    """

    def __init__(self, config: LLMConfig):
        self.use_system_prompt = False  # google gemini has no system prompt when use api

        self.__init_gemini(config)
        self.config = config
        self.model = "gemini-pro"  # so far only one model
        self.pricing_plan = self.config.pricing_plan or self.model
        self.llm = GeminiGenerativeModel(model_name=self.model)

    def __init_gemini(self, config: LLMConfig):
        genai.configure(api_key=config.api_key)

    def _user_msg(self, msg: str, images: Optional[Union[str, list[str]]] = None) -> dict[str, str]:
        # Not to change BaseLLM default functions but update with Gemini's conversation format.
        # You should follow the format.
        return {"role": "user", "parts": [msg]}

    def _assistant_msg(self, msg: str) -> dict[str, str]:
        return {"role": "model", "parts": [msg]}

    def _const_kwargs(self, messages: list[dict], stream: bool = False) -> dict:
        kwargs = {"contents": messages, "generation_config": GenerationConfig(temperature=0.3), "stream": stream}
        return kwargs

    def get_choice_text(self, resp: GenerateContentResponse) -> str:
        return resp.text

    def get_usage(self, messages: list[dict], resp_text: str) -> dict:
        req_text = messages[-1]["parts"][0] if messages else ""
        prompt_resp = self.llm.count_tokens(contents={"role": "user", "parts": [{"text": req_text}]})
        completion_resp = self.llm.count_tokens(contents={"role": "model", "parts": [{"text": resp_text}]})
        usage = {"prompt_tokens": prompt_resp.total_tokens, "completion_tokens": completion_resp.total_tokens}
        return usage

    async def aget_usage(self, messages: list[dict], resp_text: str) -> dict:
        req_text = messages[-1]["parts"][0] if messages else ""
        prompt_resp = await self.llm.count_tokens_async(contents={"role": "user", "parts": [{"text": req_text}]})
        completion_resp = await self.llm.count_tokens_async(contents={"role": "model", "parts": [{"text": resp_text}]})
        usage = {"prompt_tokens": prompt_resp.total_tokens, "completion_tokens": completion_resp.total_tokens}
        return usage

    def completion(self, messages: list[dict]) -> "GenerateContentResponse":
        resp: GenerateContentResponse = self.llm.generate_content(**self._const_kwargs(messages))
        usage = self.get_usage(messages, resp.text)
        self._update_costs(usage)
        return resp

    async def _achat_completion(self, messages: list[dict], timeout: int = 3) -> "AsyncGenerateContentResponse":
        resp: AsyncGenerateContentResponse = await self.llm.generate_content_async(**self._const_kwargs(messages))
        usage = await self.aget_usage(messages, resp.text)
        self._update_costs(usage)
        return resp

    async def acompletion(self, messages: list[dict], timeout=3) -> dict:
        return await self._achat_completion(messages, timeout=timeout)

    async def _achat_completion_stream(self, messages: list[dict], timeout: int = 3) -> str:
        resp: AsyncGenerateContentResponse = await self.llm.generate_content_async(
            **self._const_kwargs(messages, stream=True)
        )
        collected_content = []
        async for chunk in resp:
            content = chunk.text
            log_llm_stream(content)
            collected_content.append(content)
        log_llm_stream("\n")

        full_content = "".join(collected_content)
        usage = await self.aget_usage(messages, full_content)
        self._update_costs(usage)
        return full_content
