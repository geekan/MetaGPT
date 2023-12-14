#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : Google Gemini LLM from https://ai.google.dev/tutorials/python_quickstart

from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)
import google.generativeai as genai
from google.generativeai import client
from google.generativeai.types.generation_types import GenerateContentResponse, AsyncGenerateContentResponse
from google.generativeai.types.generation_types import GenerationConfig

from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.provider.base_gpt_api import BaseGPTAPI
from metagpt.provider.openai_api import log_and_reraise


class GeminiGPTAPI(BaseGPTAPI):
    """
    Refs to `https://ai.google.dev/tutorials/python_quickstart`
    """

    use_system_prompt: bool = False  # google gemini has no system prompt when use api

    def __init__(self):
        self.__init_gemini(CONFIG)
        self.model = "gemini-pro"  # so far only one model
        self.llm = genai.GenerativeModel(model_name=self.model)

    def __init_gemini(self, config: CONFIG):
        genai.configure(api_key=config.gemini_api_key)

    def _user_msg(self, msg: str) -> dict[str, str]:
        # Not to change BaseGPTAPI default functions but update with Gemini's conversation format.
        # You should follow the format.
        return {"role": "user", "parts": [msg]}

    def _assistant_msg(self, msg: str) -> dict[str, str]:
        return {"role": "model", "parts": [msg]}

    def _const_kwargs(self, messages: list[dict], stream: bool = False) -> dict:
        kwargs = {
            "contents": messages,
            "generation_config": GenerationConfig(
                temperature=0.3
            ),
            "stream": stream
        }
        return kwargs

    def _update_costs(self, usage: dict):
        """ update each request's token cost """
        if CONFIG.calc_usage:
            try:
                prompt_tokens = int(usage.get("prompt_tokens", 0))
                completion_tokens = int(usage.get("completion_tokens", 0))
                self._cost_manager.update_cost(prompt_tokens, completion_tokens, self.model)
            except Exception as e:
                logger.error("google gemini updats costs failed!", e)

    def get_choice_text(self, resp: GenerateContentResponse) -> str:
        return resp.text

    def get_usage(self, messages: list[dict], resp_text: str) -> dict:
        prompt_resp = self.llm.count_tokens(contents=messages)
        completion_resp = self.llm.count_tokens(contents={"parts": [resp_text]})
        usage = {
            "prompt_tokens": prompt_resp.total_tokens,
            "completion_tokens": completion_resp.total_tokens
        }
        return usage

    async def aget_usage(self, messages: list[dict], resp_text: str) -> dict:
        # fix google-generativeai sdk
        if self.llm._client is None:
            self.llm._client = client.get_default_generative_client()
        # TODO exception to fix
        prompt_resp = await self.llm.count_tokens_async(contents=messages)
        completion_resp = await self.llm.count_tokens_async(contents={"parts": [resp_text]})
        usage = {
            "prompt_tokens": prompt_resp.total_tokens,
            "completion_tokens": completion_resp.total_tokens
        }
        return usage

    def completion(self, messages: list[dict]) -> "GenerateContentResponse":
        resp: GenerateContentResponse = self.llm.generate_content(**self._const_kwargs(messages))
        # usage = self.get_usage(messages, resp.text)
        # self._update_costs(usage)
        return resp

    async def _achat_completion(self, messages: list[dict]) -> "AsyncGenerateContentResponse":
        resp: AsyncGenerateContentResponse = await self.llm.generate_content_async(**self._const_kwargs(messages))
        # usage = await self.aget_usage(messages, resp.text)
        # self._update_costs(usage)
        return resp

    async def acompletion(self, messages: list[dict]) -> dict:
        return await self._achat_completion(messages)

    async def _achat_completion_stream(self, messages: list[dict]) -> str:
        resp: AsyncGenerateContentResponse = await self.llm.generate_content_async(**self._const_kwargs(messages,
                                                                                                        stream=True))
        collected_content = []
        async for chunk in resp:
            content = chunk.text
            print(content, end="")
            collected_content.append(content)

        full_content = "".join(collected_content)
        # usage = await self.aget_usage(messages, full_content)
        # self._update_costs(usage)
        return full_content

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        after=after_log(logger, logger.level("WARNING").name),
        retry=retry_if_exception_type(ConnectionError),
        retry_error_callback=log_and_reraise
    )
    async def acompletion_text(self, messages: list[dict], stream=False) -> str:
        """ response in async with stream or non-stream mode """
        if stream:
            return await self._achat_completion_stream(messages)
        resp = await self._achat_completion(messages)
        return self.get_choice_text(resp)
