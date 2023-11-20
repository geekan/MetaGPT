# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/5 23:08
@Author  : alexanderwu
@File    : openai.py
@Modified By: mashenquan, 2023/8/20. Remove global configuration `CONFIG`, enable configuration support for business isolation;
            Change cost control from global to company level.
@Modified By: mashenquan, 2023/11/7. Fix bug: unclosed connection.
"""
import asyncio
import time

from openai import APIConnectionError, AsyncOpenAI, RateLimitError
from openai.types import CompletionUsage
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_fixed,
)

from metagpt.config import CONFIG
from metagpt.llm import LLMType
from metagpt.logs import logger
from metagpt.provider.base_gpt_api import BaseGPTAPI
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
        self.openai = AsyncOpenAI(api_key=CONFIG.openai_api_key)
        RateLimiter.__init__(self, rpm=self.rpm)

    async def _achat_completion_stream(self, messages: list[dict]) -> str:
        kwargs = self._cons_kwargs(messages)
        options = self._get_options()
        response = await self.openai.with_options(**options).chat.completions.create(**kwargs, stream=True)
        # iterate through the stream of events
        async for chunk in response:
            chunk_message = chunk.choices[0].delta.content or ""  # extract the message
            yield chunk_message

    def _cons_kwargs(self, messages: list[dict]) -> dict:
        if CONFIG.openai_api_type == "azure":
            kwargs = {
                "deployment_id": CONFIG.deployment_id,
                "messages": messages,
                "max_tokens": self.get_max_tokens(messages),
                "n": 1,
                "stop": None,
                "temperature": 0.3,
                "api_base": CONFIG.openai_api_base,
                "api_key": CONFIG.openai_api_key,
                "api_type": CONFIG.openai_api_type,
                "api_version": CONFIG.openai_api_version,
            }
        else:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.get_max_tokens(messages),
                "n": 1,
                "stop": None,
                "temperature": 0.3,
            }
        kwargs["timeout"] = 3

        return kwargs

    def _get_options(self):
        return CONFIG.get_openai_options()

    async def _achat_completion(self, messages: list[dict]) -> dict:
        kwargs = self._cons_kwargs(messages)
        options = self._get_options()
        rsp = await self.openai.with_options(**options).chat.completions.create(**kwargs)
        self._update_costs(rsp.usage)
        return rsp.dict()

    def completion(self, messages: list[dict]) -> dict:
        raise NotImplementedError

    async def acompletion(self, messages: list[dict]) -> dict:
        # if isinstance(messages[0], Message):
        #     messages = self.messages_to_dict(messages)
        return await self._achat_completion(messages)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        after=after_log(logger, logger.level("WARNING").name),
        retry=retry_if_exception_type(APIConnectionError),
        retry_error_callback=log_and_reraise,
    )
    @retry(
        stop=stop_after_attempt(6),
        wait=wait_exponential(1),
        after=after_log(logger, logger.level("WARNING").name),
        retry=retry_if_exception_type(RateLimitError),
        reraise=True,
    )
    async def acompletion_text(self, messages: list[dict], stream=False, generator: bool = False) -> str:
        """when streaming, print each token in place."""
        if stream:
            resp = self._achat_completion_stream(messages)
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

        rsp = await self._achat_completion(messages)
        return self.get_choice_text(rsp)

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
                logger.error("usage calculation failed!", e)
        return CompletionUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

    async def acompletion_batch(self, batch: list[list[dict]]) -> list[dict]:
        """返回完整JSON"""
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
        """仅返回纯文本"""
        raw_results = await self.acompletion_batch(batch)
        results = []
        for idx, raw_result in enumerate(raw_results, start=1):
            result = self.get_choice_text(raw_result)
            results.append(result)
            logger.info(f"Result of task {idx}: {result}")
        return results

    def _update_costs(self, usage: CompletionUsage):
        if CONFIG.calc_usage:
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            CONFIG.cost_manager.update_cost(prompt_tokens, completion_tokens, self.model)

    def get_costs(self) -> Costs:
        return CONFIG.cost_manager.get_costs()

    def get_max_tokens(self, messages: list[dict]):
        if not self.auto_max_tokens:
            return CONFIG.max_tokens_rsp
        return get_max_completion_tokens(messages, self.model, CONFIG.max_tokens_rsp)

    async def get_summary(self, text: str, max_words=200, keep_language: bool = False, **kwargs) -> str:
        from metagpt.memory.brain_memory import BrainMemory

        memory = BrainMemory(llm_type=LLMType.OPENAI.value, historical_summary=text, cacheable=False)
        return await memory.summarize(llm=self, max_words=max_words, keep_language=keep_language)

    async def close(self):
        """Close connection"""
        if not self.openai:
            return
        await self.openai.close()
        self.openai = None
