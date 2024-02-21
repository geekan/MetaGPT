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

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.const import LLM_API_TIMEOUT
from metagpt.logs import log_llm_stream, logger
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.general_api_requestor import GeneralAPIRequestor
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.provider.openai_api import log_and_reraise
from metagpt.utils.cost_manager import TokenCostManager


@register_provider(LLMType.OLLAMA)
class OllamaLLM(BaseLLM):
    """OllamaLLM is a class for interacting with the Ollama language model API.

    This class provides methods to send requests to the Ollama API for generating chat completions,
    handling streaming responses, and managing token costs associated with requests.

    Attributes:
        client: An instance of GeneralAPIRequestor configured with the base URL of the Ollama API.
        config: An LLMConfig object containing configuration settings for the Ollama API.
        suffix_url: The URL path suffix used for chat completion requests.
        http_method: The HTTP method to use for requests ('post').
        use_system_prompt: A boolean indicating whether to use the system prompt.
        _cost_manager: An instance of TokenCostManager for managing token costs.
    """

    def __init__(self, config: LLMConfig):
        """Initializes the OllamaLLM with the given configuration.

        Args:
            config: An LLMConfig object containing configuration settings for the Ollama API.
        """
        self.__init_ollama(config)
        self.client = GeneralAPIRequestor(base_url=config.base_url)
        self.config = config
        self.suffix_url = "/chat"
        self.http_method = "post"
        self.use_system_prompt = False
        self._cost_manager = TokenCostManager()

    def __init_ollama(self, config: LLMConfig):
        """Initializes Ollama specific settings.

        Args:
            config: An LLMConfig object containing configuration settings for the Ollama API.
        """
        assert config.base_url, "ollama base url is required!"
        self.model = config.model

    def _const_kwargs(self, messages: list[dict], stream: bool = False) -> dict:
        """Constructs the keyword arguments for the API request.

        Args:
            messages: A list of dictionaries representing the messages to be sent to the API.
            stream: A boolean indicating whether the request is for a streaming response.

        Returns:
            A dictionary of keyword arguments for the API request.
        """
        kwargs = {"model": self.model, "messages": messages, "options": {"temperature": 0.3}, "stream": stream}
        return kwargs

    def _update_costs(self, usage: dict):
        """Updates the token costs based on the usage information from the API response.

        Args:
            usage: A dictionary containing usage information from the API response.
        """
        if self.config.calc_usage:
            try:
                prompt_tokens = int(usage.get("prompt_tokens", 0))
                completion_tokens = int(usage.get("completion_tokens", 0))
                self._cost_manager.update_cost(prompt_tokens, completion_tokens, self.model)
            except Exception as e:
                logger.error(f"ollama updats costs failed! exp: {e}")

    def get_choice_text(self, resp: dict) -> str:
        """Extracts the choice text from the API response.

        Args:
            resp: A dictionary representing the API response.

        Returns:
            The choice text extracted from the API response.
        """
        assist_msg = resp.get("message", {})
        assert assist_msg.get("role", None) == "assistant"
        return assist_msg.get("content")

    def get_usage(self, resp: dict) -> dict:
        """Extracts the usage information from the API response.

        Args:
            resp: A dictionary representing the API response.

        Returns:
            A dictionary containing the usage information.
        """
        return {"prompt_tokens": resp.get("prompt_eval_count", 0), "completion_tokens": resp.get("eval_count", 0)}

    def _decode_and_load(self, chunk: bytes, encoding: str = "utf-8") -> dict:
        """Decodes and loads a chunk of data from the API response.

        Args:
            chunk: A bytes object representing a chunk of data from the API response.
            encoding: The encoding to use for decoding the bytes object.

        Returns:
            A dictionary representing the decoded and loaded data.
        """
        chunk = chunk.decode(encoding)
        return json.loads(chunk)

    async def _achat_completion(self, messages: list[dict]) -> dict:
        """Performs an asynchronous chat completion request.

        Args:
            messages: A list of dictionaries representing the messages to be sent to the API.

        Returns:
            A dictionary representing the API response.
        """
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
        """Performs an asynchronous completion request with a specified timeout.

        Args:
            messages: A list of dictionaries representing the messages to be sent to the API.
            timeout: The timeout in seconds for the request.

        Returns:
            A dictionary representing the API response.
        """
        return await self._achat_completion(messages)

    async def _achat_completion_stream(self, messages: list[dict]) -> str:
        """Performs an asynchronous chat completion request with streaming.

        Args:
            messages: A list of dictionaries representing the messages to be sent to the API.

        Returns:
            A string representing the full content collected from the streaming response.
        """
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
        log_llm_stream("\n")

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
        """Performs an asynchronous completion request and returns the response text.

        This method supports both streaming and non-streaming modes.

        Args:
            messages: A list of dictionaries representing the messages to be sent to the API.
            stream: A boolean indicating whether to use streaming mode.
            timeout: The timeout in seconds for the request.

        Returns:
            A string representing the response text.
        """
        if stream:
            return await self._achat_completion_stream(messages)
        resp = await self._achat_completion(messages)
        return self.get_choice_text(resp)
