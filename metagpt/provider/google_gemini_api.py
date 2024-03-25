#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : Google Gemini LLM from https://ai.google.dev/tutorials/python_quickstart
import json
import os
from dataclasses import asdict
from typing import List, Optional, Union

import google.generativeai as genai
from google.ai import generativelanguage as glm
from google.generativeai.generative_models import GenerativeModel
from google.generativeai.types import content_types
from google.generativeai.types.generation_types import (
    AsyncGenerateContentResponse,
    BlockedPromptException,
    GenerateContentResponse,
    GenerationConfig,
)

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.logs import log_llm_stream, logger
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.schema import Message


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
        if config.proxy:
            logger.info(f"Use proxy: {config.proxy}")
            os.environ["http_proxy"] = config.proxy
            os.environ["https_proxy"] = config.proxy
        genai.configure(api_key=config.api_key)

    def _user_msg(self, msg: str, images: Optional[Union[str, list[str]]] = None) -> dict[str, str]:
        # Not to change BaseLLM default functions but update with Gemini's conversation format.
        # You should follow the format.
        return {"role": "user", "parts": [msg]}

    def _assistant_msg(self, msg: str) -> dict[str, str]:
        return {"role": "model", "parts": [msg]}

    def _system_msg(self, msg: str) -> dict[str, str]:
        return {"role": "user", "parts": [msg]}

    def format_msg(self, messages: Union[str, Message, list[dict], list[Message], list[str]]) -> list[dict]:
        """convert messages to list[dict]."""
        from metagpt.schema import Message

        if not isinstance(messages, list):
            messages = [messages]

        # REF: https://ai.google.dev/tutorials/python_quickstart
        # As a dictionary, the message requires `role` and `parts` keys.
        # The role in a conversation can either be the `user`, which provides the prompts,
        # or `model`, which provides the responses.
        processed_messages = []
        for msg in messages:
            if isinstance(msg, str):
                processed_messages.append({"role": "user", "parts": [msg]})
            elif isinstance(msg, dict):
                assert set(msg.keys()) == set(["role", "parts"])
                processed_messages.append(msg)
            elif isinstance(msg, Message):
                processed_messages.append({"role": "user" if msg.role == "user" else "model", "parts": [msg.content]})
            else:
                raise ValueError(
                    f"Only support message type are: str, Message, dict, but got {type(messages).__name__}!"
                )
        return processed_messages

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

    async def _achat_completion(
        self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT
    ) -> "AsyncGenerateContentResponse":
        resp: AsyncGenerateContentResponse = await self.llm.generate_content_async(**self._const_kwargs(messages))
        usage = await self.aget_usage(messages, resp.text)
        self._update_costs(usage)
        return resp

    async def acompletion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> dict:
        return await self._achat_completion(messages, timeout=self.get_timeout(timeout))

    async def _achat_completion_stream(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> str:
        resp: AsyncGenerateContentResponse = await self.llm.generate_content_async(
            **self._const_kwargs(messages, stream=True)
        )
        collected_content = []
        async for chunk in resp:
            try:
                content = chunk.text
            except Exception as e:
                logger.warning(f"messages: {messages}\nerrors: {e}\n{BlockedPromptException(str(chunk))}")
                raise BlockedPromptException(str(chunk))
            log_llm_stream(content)
            collected_content.append(content)
        log_llm_stream("\n")

        full_content = "".join(collected_content)
        usage = await self.aget_usage(messages, full_content)
        self._update_costs(usage)
        return full_content

    def list_models(self) -> List:
        models = []
        for model in genai.list_models(page_size=100):
            models.append(asdict(model))
        logger.info(json.dumps(models))
        return models
