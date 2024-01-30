#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : Google Gemini LLM from https://ai.google.dev/tutorials/python_quickstart

import google.generativeai as genai
from google.ai import generativelanguage as glm
from google.generativeai.generative_models import GenerativeModel
from google.generativeai.types import content_types
from google.generativeai.types.generation_types import (
    AsyncGenerateContentResponse,
    GenerateContentResponse,
    GenerationConfig,
)
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.logs import log_llm_stream, logger
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.provider.openai_api import log_and_reraise


class GeminiGenerativeModel(GenerativeModel):
    """Due to `https://github.com/google/generative-ai-python/pull/123`, inherit a new class.
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
    """Refs to `https://ai.google.dev/tutorials/python_quickstart`"""

    def __init__(self, config: LLMConfig):
        """Initialize the Gemini LLM with the given configuration.

        Args:
            config: Configuration settings for the LLM.
        """
        self.use_system_prompt = False  # google gemini has no system prompt when use api

        self.__init_gemini(config)
        self.config = config
        self.model = "gemini-pro"  # so far only one model
        self.llm = GeminiGenerativeModel(model_name=self.model)

    def __init_gemini(self, config: LLMConfig):
        genai.configure(api_key=config.api_key)

    def _user_msg(self, msg: str) -> dict[str, str]:
        """Construct a user message.

        Args:
            msg: The message text.

        Returns:
            A dictionary representing the user message.
        """
        # Not to change BaseLLM default functions but update with Gemini's conversation format.
        # You should follow the format.
        return {"role": "user", "parts": [msg]}

    def _assistant_msg(self, msg: str) -> dict[str, str]:
        """Construct an assistant message.

        Args:
            msg: The message text.

        Returns:
            A dictionary representing the assistant message.
        """
        return {"role": "model", "parts": [msg]}

    def _const_kwargs(self, messages: list[dict], stream: bool = False) -> dict:
        """Construct keyword arguments for the LLM.

        Args:
            messages: A list of message dictionaries.
            stream: Whether to stream the response.

        Returns:
            A dictionary of keyword arguments for the LLM.
        """
        kwargs = {"contents": messages, "generation_config": GenerationConfig(temperature=0.3), "stream": stream}
        return kwargs

    def _update_costs(self, usage: dict):
        """Update each request's token cost.

        Args:
            usage: A dictionary containing usage information.
        """
        if self.config.calc_usage:
            try:
                prompt_tokens = int(usage.get("prompt_tokens", 0))
                completion_tokens = int(usage.get("completion_tokens", 0))
                self.cost_manager.update_cost(prompt_tokens, completion_tokens, self.model)
            except Exception as e:
                logger.error(f"google gemini updats costs failed! exp: {e}")

    def get_choice_text(self, resp: GenerateContentResponse) -> str:
        """Extract text from the response.

        Args:
            resp: The response from the LLM.

        Returns:
            The extracted text.
        """
        return resp.text

    def get_usage(self, messages: list[dict], resp_text: str) -> dict:
        """Calculate usage based on messages and response text.

        Args:
            messages: A list of message dictionaries.
            resp_text: The response text.

        Returns:
            A dictionary containing usage information.
        """
        req_text = messages[-1]["parts"][0] if messages else ""
        prompt_resp = self.llm.count_tokens(contents={"role": "user", "parts": [{"text": req_text}]})
        completion_resp = self.llm.count_tokens(contents={"role": "model", "parts": [{"text": resp_text}]})
        usage = {"prompt_tokens": prompt_resp.total_tokens, "completion_tokens": completion_resp.total_tokens}
        return usage

    async def aget_usage(self, messages: list[dict], resp_text: str) -> dict:
        """Asynchronously calculate usage based on messages and response text.

        Args:
            messages: A list of message dictionaries.
            resp_text: The response text.

        Returns:
            A dictionary containing usage information.
        """
        req_text = messages[-1]["parts"][0] if messages else ""
        prompt_resp = await self.llm.count_tokens_async(contents={"role": "user", "parts": [{"text": req_text}]})
        completion_resp = await self.llm.count_tokens_async(contents={"role": "model", "parts": [{"text": resp_text}]})
        usage = {"prompt_tokens": prompt_resp.total_tokens, "completion_tokens": completion_resp.total_tokens}
        return usage

    def completion(self, messages: list[dict]) -> "GenerateContentResponse":
        """Generate a response based on the provided messages.

        Args:
            messages: A list of message dictionaries.

        Returns:
            A GenerateContentResponse object.
        """
        resp: GenerateContentResponse = self.llm.generate_content(**self._const_kwargs(messages))
        usage = self.get_usage(messages, resp.text)
        self._update_costs(usage)
        return resp

    async def _achat_completion(self, messages: list[dict]) -> "AsyncGenerateContentResponse":
        """Asynchronously complete a chat based on the provided messages.

        Args:
            messages: A list of message dictionaries.

        Returns:
            An AsyncGenerateContentResponse object.
        """
        resp: AsyncGenerateContentResponse = await self.llm.generate_content_async(**self._const_kwargs(messages))
        usage = await self.aget_usage(messages, resp.text)
        self._update_costs(usage)
        return resp

    async def acompletion(self, messages: list[dict], timeout=3) -> dict:
        """Asynchronously complete a chat and return the response.

        Args:
            messages: A list of message dictionaries.
            timeout: The timeout in seconds.

        Returns:
            A dictionary representing the response.
        """
        return await self._achat_completion(messages)

    async def _achat_completion_stream(self, messages: list[dict]) -> str:
        """Asynchronously complete a chat with streaming and return the full content.

        Args:
            messages: A list of message dictionaries.

        Returns:
            The full content as a string.
        """
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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_random_exponential(min=1, max=60),
        after=after_log(logger, logger.level("WARNING").name),
        retry=retry_if_exception_type(ConnectionError),
        retry_error_callback=log_and_reraise,
    )
    async def acompletion_text(self, messages: list[dict], stream=False, timeout: int = 3) -> str:
        """Asynchronously generate completion text with optional streaming.

        Args:
            messages: A list of message dictionaries.
            stream: Whether to use streaming mode.
            timeout: The timeout in seconds.

        Returns:
            The generated text as a string.
        """
        if stream:
            return await self._achat_completion_stream(messages)
        resp = await self._achat_completion(messages)
        return self.get_choice_text(resp)
