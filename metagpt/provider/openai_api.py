# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/5 23:08
@Author  : alexanderwu
@File    : openai.py
@Modified By: mashenquan, 2023/8/20. Remove global configuration `CONFIG`, enable configuration support for isolation;
            Change cost control from global to company level.
@Modified By: mashenquan, 2023/11/21. Fix bug: ReadTimeout.
@Modified By: mashenquan, 2023/12/1. Fix bug: Unclosed connection caused by openai 0.x.
"""

import json
from typing import AsyncIterator, Union

from openai import APIConnectionError, AsyncOpenAI, AsyncStream
from openai._base_client import AsyncHttpxClientWrapper
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from metagpt.config import CONFIG, Config, LLMProviderEnum
from metagpt.logs import log_llm_stream, logger
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.constant import GENERAL_FUNCTION_SCHEMA, GENERAL_TOOL_CHOICE
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.schema import Message
from metagpt.utils.cost_manager import Costs
from metagpt.utils.exceptions import handle_exception
from metagpt.utils.token_counter import (
    count_message_tokens,
    count_string_tokens,
    get_max_completion_tokens,
)


def log_and_reraise(retry_state):
    logger.error(f"Retry attempts exhausted. Last exception: {retry_state.outcome.exception()}")
    logger.warning(
        """
Recommend going to https://deepwisdom.feishu.cn/wiki/MsGnwQBjiif9c3koSJNcYaoSnu4#part-XdatdVlhEojeAfxaaEZcMV3ZniQ
See FAQ 5.8
"""
    )
    raise retry_state.outcome.exception()


@register_provider(LLMProviderEnum.OPENAI)
class OpenAILLM(BaseLLM):
    """Check https://platform.openai.com/examples for examples"""

    def __init__(self):
        self.config: Config = CONFIG
        self._init_openai()
        self._init_client()
        self.auto_max_tokens = False

    def _init_openai(self):
        self.model = self.config.OPENAI_API_MODEL  # Used in _calc_usage & _cons_kwargs

    def _init_client(self):
        """https://github.com/openai/openai-python#async-usage"""
        kwargs = self._make_client_kwargs()
        self.aclient = AsyncOpenAI(**kwargs)

    def _make_client_kwargs(self) -> dict:
        kwargs = {"api_key": self.config.openai_api_key, "base_url": self.config.openai_base_url}

        # to use proxy, openai v1 needs http_client
        if proxy_params := self._get_proxy_params():
            kwargs["http_client"] = AsyncHttpxClientWrapper(**proxy_params)

        return kwargs

    def _get_proxy_params(self) -> dict:
        params = {}
        if self.config.openai_proxy:
            params = {"proxies": self.config.openai_proxy}
            if self.config.openai_base_url:
                params["base_url"] = self.config.openai_base_url

        return params

    async def _achat_completion_stream(self, messages: list[dict], timeout=3) -> AsyncIterator[str]:
        response: AsyncStream[ChatCompletionChunk] = await self.aclient.chat.completions.create(
            **self._cons_kwargs(messages, timeout=timeout), stream=True
        )

        async for chunk in response:
            chunk_message = chunk.choices[0].delta.content or "" if chunk.choices else ""  # extract the message
            yield chunk_message

    def _cons_kwargs(self, messages: list[dict], timeout=3, **extra_kwargs) -> dict:
        kwargs = {
            "messages": messages,
            "max_tokens": self._get_max_tokens(messages),
            "n": 1,
            "stop": None,
            "temperature": 0.3,
            "model": self.model,
            "timeout": max(CONFIG.timeout, timeout),
        }
        if extra_kwargs:
            kwargs.update(extra_kwargs)
        return kwargs

    async def _achat_completion(self, messages: list[dict], timeout=3) -> ChatCompletion:
        kwargs = self._cons_kwargs(messages, timeout=timeout)
        rsp: ChatCompletion = await self.aclient.chat.completions.create(**kwargs)
        self._update_costs(rsp.usage)
        return rsp

    async def acompletion(self, messages: list[dict], timeout=3) -> ChatCompletion:
        return await self._achat_completion(messages, timeout=timeout)

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
        after=after_log(logger, logger.level("WARNING").name),
        retry=retry_if_exception_type(APIConnectionError),
        retry_error_callback=log_and_reraise,
    )
    async def acompletion_text(self, messages: list[dict], stream=False, timeout=3) -> str:
        """when streaming, print each token in place."""
        if stream:
            resp = self._achat_completion_stream(messages, timeout=timeout)

            collected_messages = []
            async for i in resp:
                log_llm_stream(i)
                collected_messages.append(i)

            full_reply_content = "".join(collected_messages)
            usage = self._calc_usage(messages, full_reply_content)
            self._update_costs(usage)
            return full_reply_content

        rsp = await self._achat_completion(messages, timeout=timeout)
        return self.get_choice_text(rsp)

    def _func_configs(self, messages: list[dict], timeout=3, **kwargs) -> dict:
        """Note: Keep kwargs consistent with https://platform.openai.com/docs/api-reference/chat/create"""
        if "tools" not in kwargs:
            configs = {
                "tools": [{"type": "function", "function": GENERAL_FUNCTION_SCHEMA}],
                "tool_choice": GENERAL_TOOL_CHOICE,
            }
            kwargs.update(configs)

        return self._cons_kwargs(messages=messages, timeout=timeout, **kwargs)

    async def _achat_completion_function(self, messages: list[dict], timeout=3, **chat_configs) -> ChatCompletion:
        kwargs = self._func_configs(messages=messages, timeout=timeout, **chat_configs)
        rsp: ChatCompletion = await self.aclient.chat.completions.create(**kwargs)
        self._update_costs(rsp.usage)
        return rsp

    def _process_message(self, messages: Union[str, Message, list[dict], list[Message], list[str]]) -> list[dict]:
        """convert messages to list[dict]."""
        if isinstance(messages, list):
            messages = [Message(content=msg) if isinstance(msg, str) else msg for msg in messages]
            return [msg if isinstance(msg, dict) else msg.to_dict() for msg in messages]

        if isinstance(messages, Message):
            messages = [messages.to_dict()]
        elif isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        else:
            raise ValueError(
                f"Only support messages type are: str, Message, list[dict], but got {type(messages).__name__}!"
            )
        return messages

    async def aask_code(self, messages: Union[str, Message, list[dict]], **kwargs) -> dict:
        """Use function of tools to ask a code.
        Note: Keep kwargs consistent with https://platform.openai.com/docs/api-reference/chat/create

        Examples:
        >>> llm = OpenAILLM()
        >>> msg = [{'role': 'user', 'content': "Write a python hello world code."}]
        >>> rsp = await llm.aask_code(msg)
        # -> {'language': 'python', 'code': "print('Hello, World!')"}
        """
        messages = self._process_message(messages)
        rsp = await self._achat_completion_function(messages, **kwargs)
        return self.get_choice_function_arguments(rsp)

    @handle_exception
    def get_choice_function_arguments(self, rsp: ChatCompletion) -> dict:
        """Required to provide the first function arguments of choice.

        :return dict: return the first function arguments of choice, for example,
            {'language': 'python', 'code': "print('Hello, World!')"}
        """
        return json.loads(rsp.choices[0].message.tool_calls[0].function.arguments)

    def get_choice_text(self, rsp: ChatCompletion) -> str:
        """Required to provide the first text of choice"""
        return rsp.choices[0].message.content if rsp.choices else ""

    def _calc_usage(self, messages: list[dict], rsp: str) -> CompletionUsage:
        usage = CompletionUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        if not CONFIG.calc_usage:
            return usage

        try:
            usage.prompt_tokens = count_message_tokens(messages, self.model)
            usage.completion_tokens = count_string_tokens(rsp, self.model)
        except Exception as e:
            logger.error(f"usage calculation failed: {e}")

        return usage

    @handle_exception
    def _update_costs(self, usage: CompletionUsage):
        if CONFIG.calc_usage and usage:
            CONFIG.cost_manager.update_cost(usage.prompt_tokens, usage.completion_tokens, self.model)

    def get_costs(self) -> Costs:
        return CONFIG.cost_manager.get_costs()

    def _get_max_tokens(self, messages: list[dict]):
        if not self.auto_max_tokens:
            return CONFIG.max_tokens_rsp
        return get_max_completion_tokens(messages, self.model, CONFIG.max_tokens_rsp)

    @handle_exception
    async def amoderation(self, content: Union[str, list[str]]):
        """Moderate content."""
        return await self.aclient.moderations.create(input=content)
