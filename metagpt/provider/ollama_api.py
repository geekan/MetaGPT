#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : self-host open llm model with ollama which isn't openai-api-compatible

import json
from typing import AsyncGenerator, Tuple

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.logs import log_llm_stream
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.general_api_requestor import GeneralAPIRequestor, OpenAIResponse
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.utils.cost_manager import TokenCostManager


@register_provider(LLMType.OLLAMA)
class OllamaLLM(BaseLLM):
    """
    Refs to `https://github.com/jmorganca/ollama/blob/main/docs/api.md#generate-a-chat-completion`
    """

    def __init__(self, config: LLMConfig):
        self.__init_ollama(config)
        self.client = GeneralAPIRequestor(base_url=config.base_url)
        self.config = config
        self.suffix_url = "/chat"
        self.http_method = "post"
        self.use_system_prompt = False
        self.cost_manager = TokenCostManager()

    def __init_ollama(self, config: LLMConfig):
        assert config.base_url, "ollama base url is required!"
        self.model = config.model
        self.pricing_plan = self.model

    def _const_kwargs(self, messages: list[dict], stream: bool = False) -> dict:
        return {"model": self.model, "messages": messages, "options": {"temperature": 0.3}, "stream": stream}

    def get_choice_text(self, resp: dict) -> str:
        """get the resp content from llm response"""
        assist_msg = resp.get("message", {})
        if assist_msg.get("role", None) == "assistant":  # chat
            return assist_msg.get("content")
        else:  # llava
            return resp["response"]

    def get_usage(self, resp: dict) -> dict:
        return {"prompt_tokens": resp.get("prompt_eval_count", 0), "completion_tokens": resp.get("eval_count", 0)}

    def _decode_and_load(self, openai_resp: OpenAIResponse, encoding: str = "utf-8") -> dict:
        return json.loads(openai_resp.data.decode(encoding))

    async def _achat_completion(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> dict:
        messages, fixed_suffix_url = self._apply_llava(messages)
        resp, _, _ = await self.client.arequest(
            method=self.http_method,
            url=fixed_suffix_url,
            headers=self._get_headers(),
            params=messages,
            request_timeout=self.get_timeout(timeout),
        )
        if isinstance(resp, AsyncGenerator):
            return await self._processing_openai_response_async_generator(resp)
        elif isinstance(resp, OpenAIResponse):
            return self._processing_openai_response(resp)
        else:
            raise NotImplementedError

    async def acompletion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> dict:
        return await self._achat_completion(messages, timeout=self.get_timeout(timeout))

    async def _achat_completion_stream(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> str:
        messages, fixed_suffix_url = self._apply_llava(messages, stream=True)
        stream_resp, _, _ = await self.client.arequest(
            method=self.http_method,
            url=fixed_suffix_url,
            headers=self._get_headers(),
            stream=True,
            params=messages,
            request_timeout=self.get_timeout(timeout),
        )
        if isinstance(stream_resp, AsyncGenerator):
            return await self._processing_openai_response_async_generator(stream_resp)
        elif isinstance(stream_resp, OpenAIResponse):
            return self._processing_openai_response(stream_resp)
        else:
            raise NotImplementedError

    def _processing_openai_response(self, openai_resp: OpenAIResponse):
        resp = self._decode_and_load(openai_resp)
        usage = self.get_usage(resp)
        self._update_costs(usage)
        return resp

    async def _processing_openai_response_async_generator(self, ag_openai_resp: AsyncGenerator[OpenAIResponse, None]):
        collected_content = []
        usage = {}
        async for raw_chunk in ag_openai_resp:
            chunk = self._decode_and_load(raw_chunk)

            if not chunk.get("done", False):
                content = self.get_choice_text(chunk)
                collected_content.append(content)
                log_llm_stream(content)
            else:
                # stream finished
                usage = self.get_usage(chunk)
        log_llm_stream("\n")

        self._update_costs(usage)
        full_content = "".join(collected_content)
        return full_content

    def _get_headers(self):
        return (
            None
            if not self.config.api_key or self.config.api_key == "sk-"
            else {"Authorization": f"Bearer {self.config.api_key}"}
        )

    def _apply_llava(self, messages: list[dict], stream: bool = False) -> Tuple[dict, str]:
        llava = False
        if isinstance(messages[0]["content"], str):
            return self._const_kwargs(messages, stream), self.suffix_url

        if any(len(msg["content"]) >= 2 for msg in messages):
            assert all(len(msg["content"]) >= 2 for msg in messages), "input should have the same api type"
            llava = True
        if not llava:
            return self._const_kwargs(messages, stream), self.suffix_url

        assert len(messages) <= 1, "not support batch massages in llava calling images"
        contents = messages[0]["content"]
        return {
            "model": self.model,
            "prompt": contents[0]["text"],
            "images": [i["image_url"]["url"][23:] for i in contents[1:]],
        }, "/generate"
