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
import time
from typing import Union

import openai
from openai import APIConnectionError, AsyncAzureOpenAI, AsyncOpenAI, RateLimitError
from openai.types import CompletionUsage
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.provider import LLMType
from metagpt.provider.base_gpt_api import BaseGPTAPI
from metagpt.provider.constant import GENERAL_FUNCTION_SCHEMA, GENERAL_TOOL_CHOICE
from metagpt.schema import Message
from metagpt.utils.cost_manager import Costs
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


class OpenAIGPTAPI(BaseGPTAPI, RateLimiter):
    """
    Check https://platform.openai.com/examples for examples
    """

    def __init__(self):
        self.model = CONFIG.openai_api_model
        self.auto_max_tokens = False
        self.rpm = int(CONFIG.get("RPM", 10))
        if CONFIG.openai_api_type == "azure":
            # https://learn.microsoft.com/zh-cn/azure/ai-services/openai/how-to/migration?tabs=python-new%2Cdalle-fix
            self._client = AsyncAzureOpenAI(
                api_key=CONFIG.openai_api_key,
                api_version=CONFIG.openai_api_version,
                azure_endpoint=CONFIG.openai_api_base,
            )
        else:
            # https://github.com/openai/openai-python#async-usage
            self._client = AsyncOpenAI(api_key=CONFIG.openai_api_key, base_url=CONFIG.openai_api_base)
        RateLimiter.__init__(self, rpm=self.rpm)

    async def _achat_completion_stream(self, messages: list[dict], timeout=3) -> str:
        kwargs = self._cons_kwargs(messages, timeout=timeout)
        response = await self._client.chat.completions.create(**kwargs, stream=True)
        # iterate through the stream of events
        async for chunk in response:
            chunk_message = chunk.choices[0].delta.content or ""  # extract the message
            yield chunk_message

    def _cons_kwargs(self, messages: list[dict], timeout=3, **configs) -> dict:
        kwargs = {
            "messages": messages,
            "max_tokens": self.get_max_tokens(messages),
            "n": 1,
            "stop": None,
            "temperature": 0.3,
        }
        if configs:
            kwargs.update(configs)

        if CONFIG.openai_api_type == "azure":
            kwargs["model"] = CONFIG.deployment_id
        else:
            kwargs["model"] = self.model
        try:
            default_timeout = int(CONFIG.TIMEOUT) if CONFIG.TIMEOUT else 0
        except ValueError:
            default_timeout = 0
        kwargs["timeout"] = max(default_timeout, timeout)

        return kwargs

    async def _achat_completion(self, messages: list[dict], timeout=3) -> dict:
        kwargs = self._cons_kwargs(messages, timeout=timeout)
        rsp = await self._client.chat.completions.create(**kwargs)
        self._update_costs(rsp.usage)
        return rsp.dict()

    def completion(self, messages: list[dict], timeout=3) -> dict:
        loop = self.get_event_loop()
        return loop.run_until_complete(self.acompletion(messages, timeout=timeout))

    async def acompletion(self, messages: list[dict], timeout=3) -> dict:
        # if isinstance(messages[0], Message):
        #     messages = self.messages_to_dict(messages)
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

    def _chat_completion_function(self, messages: list[dict], timeout=3, **kwargs) -> dict:
        loop = self.get_event_loop()
        return loop.run_until_complete(self._achat_completion_function(messages=messages, timeout=timeout, **kwargs))

    async def _achat_completion_function(self, messages: list[dict], timeout=3, **chat_configs) -> dict:
        kwargs = self._func_configs(messages=messages, timeout=timeout, **chat_configs)
        rsp = await self._client.chat.completions.create(**kwargs)
        self._update_costs(rsp.usage)
        return rsp.dict()

    def _process_message(self, messages: Union[str, Message, list[dict], list[Message], list[str]]) -> list[dict]:
        """convert messages to list[dict]."""
        if isinstance(messages, list):
            messages = [Message(msg) if isinstance(msg, str) else msg for msg in messages]
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

    async def acompletion_batch(self, batch: list[list[dict]], timeout=3) -> list[dict]:
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
        if CONFIG.calc_usage:
            try:
                prompt_tokens = usage.prompt_tokens
                completion_tokens = usage.completion_tokens
                CONFIG.cost_manager.update_cost(prompt_tokens, completion_tokens, self.model)
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

    async def amoderation(self, content: Union[str, list[str]]):
        try:
            if not content:
                logger.error("content cannot be empty!")
            else:
                rsp = await self._amoderation(content=content)
                return rsp
        except Exception as e:
            logger.error(f"moderating failed:{e}")

    async def _amoderation(self, content: Union[str, list[str]]):
        rsp = await self._client.moderations.create(input=content)
        return rsp

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

    async def get_summary(self, text: str, max_words=200, keep_language: bool = False, **kwargs) -> str:
        from metagpt.memory.brain_memory import BrainMemory

        memory = BrainMemory(llm_type=LLMType.OPENAI.value, historical_summary=text, cacheable=False)
        return await memory.summarize(llm=self, max_words=max_words, keep_language=keep_language)
