# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/5 23:08
@Author  : alexanderwu
@File    : openai.py
@Modified By: mashenquan, 2023/8/20. Remove global configuration `CONFIG`, enable configuration support for business isolation;
            Change cost control from global to company level.
@Modified By: mashenquan, 2023/11/21. Fix bug: ReadTimeout.
@Modified By: mashenquan, 2023/12/1. Fix bug: Unclosed connection caused by openai 0.x.
"""

import asyncio
import json
import time
from typing import List, Union

import openai
from openai import APIConnectionError, AsyncOpenAI, AsyncStream, OpenAI, RateLimitError
from openai._base_client import AsyncHttpxClientWrapper, SyncHttpxClientWrapper
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
from metagpt.const import DEFAULT_MAX_TOKENS
from metagpt.logs import logger
from metagpt.provider.base_gpt_api import BaseGPTAPI
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


class RateLimiter:
    """Rate control class, each call goes through wait_if_needed, sleep if rate control is needed"""

    def __init__(self, rpm):
        self.last_call_time = 0
        # Here 1.1 is used because even if the calls are made strictly according to time,
        # they will still be QOS'd; consider switching to simple error retry later
        self.interval = 1.1 * 60 / rpm
        self.rpm = rpm

    def split_batches(self, batch):
        return [batch[i : i + self.rpm] for i in range(0, len(batch), self.rpm)]

    async def wait_if_needed(self, num_requests):
        current_time = time.time()
        elapsed_time = current_time - self.last_call_time

        if elapsed_time < self.interval * num_requests:
            remaining_time = self.interval * num_requests - elapsed_time
            logger.info(f"sleep {remaining_time}")
            await asyncio.sleep(remaining_time)

        self.last_call_time = time.time()


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
class OpenAIGPTAPI(BaseGPTAPI, RateLimiter):
    """
    Check https://platform.openai.com/examples for examples
    """

    def __init__(self):
        self.config: Config = CONFIG
        self.__init_openai()
        self.auto_max_tokens = False
        # https://github.com/openai/openai-python#async-usage
        self._client = AsyncOpenAI(api_key=CONFIG.openai_api_key, base_url=CONFIG.openai_api_base)
        RateLimiter.__init__(self, rpm=self.rpm)

    # async def _achat_completion_stream(self, messages: list[dict], timeout=3) -> str:
    #     kwargs = self._cons_kwargs(messages, timeout=timeout)
    #     response = await self._client.chat.completions.create(**kwargs, stream=True)
    #     # iterate through the stream of events
    #     async for chunk in response:
    #         chunk_message = chunk.choices[0].delta.content or ""  # extract the message
    #         yield chunk_message

    def __init_openai(self):
        self.rpm = int(self.config.get("RPM", 10))
        self._make_client()

    def _make_client(self):
        kwargs, async_kwargs = self._make_client_kwargs()
        self.client = OpenAI(**kwargs)
        self.async_client = AsyncOpenAI(**async_kwargs)

    def _make_client_kwargs(self) -> (dict, dict):
        kwargs = dict(api_key=self.config.openai_api_key, base_url=self.config.openai_base_url)
        async_kwargs = kwargs.copy()

        # to use proxy, openai v1 needs http_client
        proxy_params = self._get_proxy_params()
        if proxy_params:
            kwargs["http_client"] = SyncHttpxClientWrapper(**proxy_params)
            async_kwargs["http_client"] = AsyncHttpxClientWrapper(**proxy_params)

        return kwargs, async_kwargs

    def _get_proxy_params(self) -> dict:
        params = {}
        if self.config.openai_proxy:
            params = {"proxies": self.config.openai_proxy}
            if self.config.openai_base_url:
                params["base_url"] = self.config.openai_base_url

        return params

    async def _achat_completion_stream(self, messages: list[dict], timeout=3) -> str:
        response: AsyncStream[ChatCompletionChunk] = await self._client.chat.completions.create(
            **self._cons_kwargs(messages, timeout=timeout), stream=True
        )

        # create variables to collect the stream of chunks
        collected_chunks = []
        collected_messages = []
        # iterate through the stream of events
        async for chunk in response:
            collected_chunks.append(chunk)  # save the event response
            if chunk.choices:
                chunk_message = chunk.choices[0].delta  # extract the message
                collected_messages.append(chunk_message)  # save the message
                if chunk_message.content:
                    print(chunk_message.content, end="")
        print()

        full_reply_content = "".join([m.content for m in collected_messages if m.content])
        usage = self._calc_usage(messages, full_reply_content)
        self._update_costs(usage)
        return full_reply_content

    def _cons_kwargs(self, messages: list[dict], timeout=3, **configs) -> dict:
        kwargs = {
            "messages": messages,
            "max_tokens": self.get_max_tokens(messages),
            "n": 1,
            "stop": None,
            "temperature": 0.3,
            "model": self.config.openai_api_model,
        }
        if configs:
            kwargs.update(configs)
        try:
            default_timeout = int(CONFIG.TIMEOUT) if CONFIG.TIMEOUT else 0
        except ValueError:
            default_timeout = 0
        kwargs["timeout"] = max(default_timeout, timeout)

        return kwargs

    async def _achat_completion(self, messages: list[dict], timeout=3) -> ChatCompletion:
        kwargs = self._cons_kwargs(messages, timeout=timeout)
        rsp: ChatCompletion = await self._client.chat.completions.create(**kwargs)
        self._update_costs(rsp.usage)
        return rsp

    def completion(self, messages: list[dict], timeout=3) -> ChatCompletion:
        loop = self.get_event_loop()
        return loop.run_until_complete(self.acompletion(messages, timeout=timeout))

    async def acompletion(self, messages: list[dict], timeout=3) -> ChatCompletion:
        return await self._achat_completion(messages, timeout=timeout)

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
        after=after_log(logger, logger.level("WARNING").name),
        retry=retry_if_exception_type(APIConnectionError),
        retry_error_callback=log_and_reraise,
    )
    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
        after=after_log(logger, logger.level("WARNING").name),
        retry=retry_if_exception_type(RateLimitError),
        reraise=True,
    )
    async def acompletion_text(self, messages: list[dict], stream=False, generator: bool = False, timeout=3) -> str:
        """when streaming, print each token in place."""
        if stream:
            resp = self._achat_completion_stream(messages, timeout=timeout)
            if generator:
                return resp

            collected_messages = []
            async for i in resp:
                print(i, end="")
                collected_messages.append(i)

            full_reply_content = "".join(collected_messages)
            usage = self._calc_usage(messages, full_reply_content)
            self._update_costs(usage)
            return full_reply_content

        rsp = await self._achat_completion(messages, timeout=timeout)
        return self.get_choice_text(rsp)

    def _func_configs(self, messages: list[dict], timeout=3, **kwargs) -> dict:
        """
        Note: Keep kwargs consistent with the parameters in the https://platform.openai.com/docs/api-reference/chat/create
        """
        if "tools" not in kwargs:
            configs = {
                "tools": [{"type": "function", "function": GENERAL_FUNCTION_SCHEMA}],
                "tool_choice": GENERAL_TOOL_CHOICE,
            }
            kwargs.update(configs)

        return self._cons_kwargs(messages=messages, timeout=timeout, **kwargs)

    def _chat_completion_function(self, messages: list[dict], timeout=3, **kwargs) -> ChatCompletion:
        loop = self.get_event_loop()
        return loop.run_until_complete(self._achat_completion_function(messages=messages, timeout=timeout, **kwargs))

    async def _achat_completion_function(self, messages: list[dict], timeout=3, **chat_configs) -> ChatCompletion:
        kwargs = self._func_configs(messages=messages, timeout=timeout, **chat_configs)
        rsp: ChatCompletion = await self._client.chat.completions.create(**kwargs)
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

    def ask_code(self, messages: Union[str, Message, list[dict]], **kwargs) -> dict:
        """Use function of tools to ask a code.

        Note: Keep kwargs consistent with the parameters in the https://platform.openai.com/docs/api-reference/chat/create

        Examples:

        >>> llm = OpenAIGPTAPI()
        >>> llm.ask_code("Write a python hello world code.")
        {'language': 'python', 'code': "print('Hello, World!')"}
        >>> msg = [{'role': 'user', 'content': "Write a python hello world code."}]
        >>> llm.ask_code(msg)
        {'language': 'python', 'code': "print('Hello, World!')"}
        """
        messages = self._process_message(messages)
        rsp = self._chat_completion_function(messages, **kwargs)
        return self.get_choice_function_arguments(rsp)

    async def aask_code(self, messages: Union[str, Message, list[dict]], **kwargs) -> dict:
        """Use function of tools to ask a code.

        Note: Keep kwargs consistent with the parameters in the https://platform.openai.com/docs/api-reference/chat/create

        Examples:

        >>> llm = OpenAIGPTAPI()
        >>> rsp = await llm.ask_code("Write a python hello world code.")
        >>> rsp
        {'language': 'python', 'code': "print('Hello, World!')"}
        >>> msg = [{'role': 'user', 'content': "Write a python hello world code."}]
        >>> rsp = await llm.aask_code(msg)   # -> {'language': 'python', 'code': "print('Hello, World!')"}
        """
        messages = self._process_message(messages)
        try:
            rsp = await self._achat_completion_function(messages, **kwargs)
            return self.get_choice_function_arguments(rsp)
        except openai.NotFoundError as e:
            logger.error(f"API TYPE:{CONFIG.openai_api_type}, err:{e}")
            raise e

    def _calc_usage(self, messages: list[dict], rsp: str) -> CompletionUsage:
        if CONFIG.calc_usage:
            try:
                prompt_tokens = count_message_tokens(messages, self.model)
                completion_tokens = count_string_tokens(rsp, self.model)
                usage = CompletionUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                )
                return usage
            except Exception as e:
                logger.error(f"{self.model} usage calculation failed!", e)
        return CompletionUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

    def get_choice_function_arguments(self, rsp: ChatCompletion) -> dict:
        """Required to provide the first function arguments of choice.

        :return dict: return the first function arguments of choice, for example,
            {'language': 'python', 'code': "print('Hello, World!')"}
        """
        try:
            return json.loads(rsp.choices[0].message.tool_calls[0].function.arguments)
        except json.JSONDecodeError:
            return {}

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
            logger.error(f"usage calculation failed!: {e}")

        return usage

    async def acompletion_batch(self, batch: list[list[dict]], timeout=3) -> list[ChatCompletion]:
        """Return full JSON"""
        split_batches = self.split_batches(batch)
        all_results = []

        for small_batch in split_batches:
            logger.info(small_batch)
            await self.wait_if_needed(len(small_batch))

            future = [self.acompletion(prompt, timeout=timeout) for prompt in small_batch]
            results = await asyncio.gather(*future)
            logger.info(results)
            all_results.extend(results)

        return all_results

    async def acompletion_batch_text(self, batch: list[list[dict]], timeout=3) -> list[str]:
        """Only return plain text"""
        raw_results = await self.acompletion_batch(batch, timeout=timeout)
        results = []
        for idx, raw_result in enumerate(raw_results, start=1):
            result = self.get_choice_text(raw_result)
            results.append(result)
            logger.info(f"Result of task {idx}: {result}")
        return results

    def _update_costs(self, usage: CompletionUsage):
        if CONFIG.calc_usage and usage:
            try:
                CONFIG.cost_manager.update_cost(usage.prompt_tokens, usage.completion_tokens, self.model)
            except Exception as e:
                logger.error("updating costs failed!", e)

    def get_costs(self) -> Costs:
        return CONFIG.cost_manager.get_costs()

    def get_max_tokens(self, messages: list[dict]):
        if not self.auto_max_tokens:
            return CONFIG.max_tokens_rsp
        return get_max_completion_tokens(messages, self.model, CONFIG.max_tokens_rsp)

    def moderation(self, content: Union[str, list[str]]):
        loop = self.get_event_loop()
        loop.run_until_complete(self.amoderation(content=content))

    @handle_exception
    async def amoderation(self, content: Union[str, list[str]]):
        return await self._client.moderations.create(input=content)

    async def close(self):
        """Close connection"""
        if not self._client:
            return
        await self._client.close()
        self._client = None

    @staticmethod
    def get_event_loop():
        try:
            return asyncio.get_event_loop()
        except RuntimeError as e:
            if "There is no current event loop in thread" in str(e):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return loop
            else:
                raise e

    async def summarize(self, text: str, max_words=200, keep_language: bool = False, limit: int = -1, **kwargs) -> str:
        max_token_count = DEFAULT_MAX_TOKENS
        max_count = 100
        text_length = len(text)
        if limit > 0 and text_length < limit:
            return text
        summary = ""
        while max_count > 0:
            if text_length < max_token_count:
                summary = await self._get_summary(text=text, max_words=max_words, keep_language=keep_language)
                break

            padding_size = 20 if max_token_count > 20 else 0
            text_windows = self.split_texts(text, window_size=max_token_count - padding_size)
            part_max_words = min(int(max_words / len(text_windows)) + 1, 100)
            summaries = []
            for ws in text_windows:
                response = await self._get_summary(text=ws, max_words=part_max_words, keep_language=keep_language)
                summaries.append(response)
            if len(summaries) == 1:
                summary = summaries[0]
                break

            # Merged and retry
            text = "\n".join(summaries)
            text_length = len(text)

            max_count -= 1  # safeguard
        return summary

    async def _get_summary(self, text: str, max_words=20, keep_language: bool = False):
        """Generate text summary"""
        if len(text) < max_words:
            return text
        if keep_language:
            command = f".Translate the above content into a summary of less than {max_words} words in language of the content strictly."
        else:
            command = f"Translate the above content into a summary of less than {max_words} words."
        msg = text + "\n\n" + command
        logger.debug(f"summary ask:{msg}")
        response = await self.aask(msg=msg, system_msgs=[])
        logger.debug(f"summary rsp: {response}")
        return response

    @staticmethod
    def split_texts(text: str, window_size) -> List[str]:
        """Splitting long text into sliding windows text"""
        if window_size <= 0:
            window_size = DEFAULT_TOKEN_SIZE
        total_len = len(text)
        if total_len <= window_size:
            return [text]

        padding_size = 20 if window_size > 20 else 0
        windows = []
        idx = 0
        data_len = window_size - padding_size
        while idx < total_len:
            if window_size + idx > total_len:  # 不足一个滑窗
                windows.append(text[idx:])
                break
            # 每个窗口少算padding_size自然就可实现滑窗功能, 比如: [1, 2, 3, 4, 5, 6, 7, ....]
            # window_size=3, padding_size=1：
            # [1, 2, 3], [3, 4, 5], [5, 6, 7], ....
            #   idx=2,  |  idx=5   |  idx=8  | ...
            w = text[idx : idx + window_size]
            windows.append(w)
            idx += data_len

        return windows
