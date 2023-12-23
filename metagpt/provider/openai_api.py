# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/5 23:08
@Author  : alexanderwu
@File    : openai.py
"""
import asyncio
import json
import time
from typing import NamedTuple, Union

from openai import (
    APIConnectionError,
    AsyncAzureOpenAI,
    AsyncOpenAI,
    AsyncStream,
    AzureOpenAI,
    OpenAI,
)
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
from metagpt.logs import log_llm_stream, logger
from metagpt.provider.base_gpt_api import BaseGPTAPI
from metagpt.provider.constant import GENERAL_FUNCTION_SCHEMA, GENERAL_TOOL_CHOICE
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.schema import Message
from metagpt.utils.exceptions import handle_exception
from metagpt.utils.singleton import Singleton
from metagpt.utils.token_counter import (
    TOKEN_COSTS,
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


class Costs(NamedTuple):
    total_prompt_tokens: int
    total_completion_tokens: int
    total_cost: float
    total_budget: float


class CostManager(metaclass=Singleton):
    """计算使用接口的开销"""

    def __init__(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0
        self.total_budget = 0

    def update_cost(self, prompt_tokens, completion_tokens, model):
        """
        Update the total cost, prompt tokens, and completion tokens.

        Args:
        prompt_tokens (int): The number of tokens used in the prompt.
        completion_tokens (int): The number of tokens used in the completion.
        model (str): The model used for the API call.
        """
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        cost = (
            prompt_tokens * TOKEN_COSTS[model]["prompt"] + completion_tokens * TOKEN_COSTS[model]["completion"]
        ) / 1000
        self.total_cost += cost
        logger.info(
            f"Total running cost: ${self.total_cost:.3f} | Max budget: ${CONFIG.max_budget:.3f} | "
            f"Current cost: ${cost:.3f}, prompt_tokens: {prompt_tokens}, completion_tokens: {completion_tokens}"
        )
        CONFIG.total_cost = self.total_cost

    def get_total_prompt_tokens(self):
        """
        Get the total number of prompt tokens.

        Returns:
        int: The total number of prompt tokens.
        """
        return self.total_prompt_tokens

    def get_total_completion_tokens(self):
        """
        Get the total number of completion tokens.

        Returns:
        int: The total number of completion tokens.
        """
        return self.total_completion_tokens

    def get_total_cost(self):
        """
        Get the total cost of API calls.

        Returns:
        float: The total cost of API calls.
        """
        return self.total_cost

    def get_costs(self) -> Costs:
        """Get all costs"""
        return Costs(self.total_prompt_tokens, self.total_completion_tokens, self.total_cost, self.total_budget)


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
        self._cost_manager = CostManager()
        RateLimiter.__init__(self, rpm=self.rpm)

    def __init_openai(self):
        self.is_azure = self.config.openai_api_type == "azure"
        self.model = self.config.deployment_name if self.is_azure else self.config.openai_api_model
        self.rpm = int(self.config.get("RPM", 10))
        self._make_client()

    def _make_client(self):
        kwargs, async_kwargs = self._make_client_kwargs()

        if self.is_azure:
            self.client = AzureOpenAI(**kwargs)
            self.async_client = AsyncAzureOpenAI(**async_kwargs)
        else:
            self.client = OpenAI(**kwargs)
            self.async_client = AsyncOpenAI(**async_kwargs)

    def _make_client_kwargs(self) -> (dict, dict):
        if self.is_azure:
            kwargs = dict(
                api_key=self.config.openai_api_key,
                api_version=self.config.openai_api_version,
                azure_endpoint=self.config.openai_base_url,
            )
        else:
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

    async def _achat_completion_stream(self, messages: list[dict]) -> str:
        response: AsyncStream[ChatCompletionChunk] = await self.async_client.chat.completions.create(
            **self._cons_kwargs(messages), stream=True
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
                    log_llm_stream(chunk_message.content)
        print()

        full_reply_content = "".join([m.content for m in collected_messages if m.content])
        usage = self._calc_usage(messages, full_reply_content)
        self._update_costs(usage)
        return full_reply_content

    def _cons_kwargs(self, messages: list[dict], **configs) -> dict:
        kwargs = {
            "messages": messages,
            "max_tokens": self.get_max_tokens(messages),
            "n": 1,
            "stop": None,
            "temperature": 0.3,
            "timeout": 3,
            "model": self.model,
        }
        if configs:
            kwargs.update(configs)

        return kwargs

    async def _achat_completion(self, messages: list[dict]) -> ChatCompletion:
        rsp: ChatCompletion = await self.async_client.chat.completions.create(**self._cons_kwargs(messages))
        self._update_costs(rsp.usage)
        return rsp

    def _chat_completion(self, messages: list[dict]) -> ChatCompletion:
        rsp: ChatCompletion = self.client.chat.completions.create(**self._cons_kwargs(messages))
        self._update_costs(rsp.usage)
        return rsp

    def completion(self, messages: list[dict]) -> ChatCompletion:
        return self._chat_completion(messages)

    async def acompletion(self, messages: list[dict]) -> ChatCompletion:
        return await self._achat_completion(messages)

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
        after=after_log(logger, logger.level("WARNING").name),
        retry=retry_if_exception_type(APIConnectionError),
        retry_error_callback=log_and_reraise,
    )
    async def acompletion_text(self, messages: list[dict], stream=False) -> str:
        """when streaming, print each token in place."""
        if stream:
            return await self._achat_completion_stream(messages)
        rsp = await self._achat_completion(messages)
        return self.get_choice_text(rsp)

    def _func_configs(self, messages: list[dict], **kwargs) -> dict:
        """
        Note: Keep kwargs consistent with the parameters in the https://platform.openai.com/docs/api-reference/chat/create
        """
        if "tools" not in kwargs:
            configs = {
                "tools": [{"type": "function", "function": GENERAL_FUNCTION_SCHEMA}],
                "tool_choice": GENERAL_TOOL_CHOICE,
            }
            kwargs.update(configs)

        return self._cons_kwargs(messages, **kwargs)

    def _chat_completion_function(self, messages: list[dict], **kwargs) -> ChatCompletion:
        rsp: ChatCompletion = self.client.chat.completions.create(**self._func_configs(messages, **kwargs))
        self._update_costs(rsp.usage)
        return rsp

    async def _achat_completion_function(self, messages: list[dict], **chat_configs) -> ChatCompletion:
        rsp: ChatCompletion = await self.async_client.chat.completions.create(
            **self._func_configs(messages, **chat_configs)
        )
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
        rsp = await self._achat_completion_function(messages, **kwargs)
        return self.get_choice_function_arguments(rsp)

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

    async def acompletion_batch(self, batch: list[list[dict]]) -> list[ChatCompletion]:
        """Return full JSON"""
        split_batches = self.split_batches(batch)
        all_results = []

        for small_batch in split_batches:
            logger.info(small_batch)
            await self.wait_if_needed(len(small_batch))

            future = [self.acompletion(prompt) for prompt in small_batch]
            results = await asyncio.gather(*future)
            logger.info(results)
            all_results.extend(results)

        return all_results

    async def acompletion_batch_text(self, batch: list[list[dict]]) -> list[str]:
        """Only return plain text"""
        raw_results = await self.acompletion_batch(batch)
        results = []
        for idx, raw_result in enumerate(raw_results, start=1):
            result = self.get_choice_text(raw_result)
            results.append(result)
            logger.info(f"Result of task {idx}: {result}")
        return results

    def _update_costs(self, usage: CompletionUsage):
        if CONFIG.calc_usage and usage:
            try:
                self._cost_manager.update_cost(usage.prompt_tokens, usage.completion_tokens, self.model)
            except Exception as e:
                logger.error("updating costs failed!", e)

    def get_costs(self) -> Costs:
        return self._cost_manager.get_costs()

    def get_max_tokens(self, messages: list[dict]):
        if not self.auto_max_tokens:
            return CONFIG.max_tokens_rsp
        return get_max_completion_tokens(messages, self.model, CONFIG.max_tokens_rsp)

    @handle_exception
    async def amoderation(self, content: Union[str, list[str]]):
        return await self.async_client.moderations.create(input=content)
