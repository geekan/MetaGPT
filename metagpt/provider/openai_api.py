# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/5 23:08
@Author  : alexanderwu
@File    : openai.py
@Modified By: mashenquan, 2023/8/20. Remove global configuration `CONFIG`, enable configuration support for business isolation;
            Change cost control from global to company level.
"""
import asyncio
import random
import re
import time
import traceback
from typing import List

import openai
from openai.error import APIConnectionError
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from metagpt.config import CONFIG
from metagpt.const import DEFAULT_LANGUAGE, DEFAULT_MAX_TOKENS
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
        self.__init_openai(CONFIG)
        self.llm = openai
        self.model = CONFIG.openai_api_model
        self.auto_max_tokens = False
        RateLimiter.__init__(self, rpm=self.rpm)

    def __init_openai(self, config):
        openai.api_key = config.openai_api_key
        if config.openai_api_base:
            openai.api_base = config.openai_api_base
        if config.openai_api_type:
            openai.api_type = config.openai_api_type
            openai.api_version = config.openai_api_version
        self.rpm = int(config.get("RPM", 10))

    async def _achat_completion_stream(self, messages: list[dict]) -> str:
        response = await self.async_retry_call(
            openai.ChatCompletion.acreate, **self._cons_kwargs(messages), stream=True
        )
        # create variables to collect the stream of chunks
        collected_chunks = []
        collected_messages = []
        # iterate through the stream of events
        async for chunk in response:
            collected_chunks.append(chunk)  # save the event response
            chunk_message = chunk["choices"][0]["delta"]  # extract the message
            collected_messages.append(chunk_message)  # save the message
            if "content" in chunk_message:
                print(chunk_message["content"], end="")
        print()

        full_reply_content = "".join([m.get("content", "") for m in collected_messages])
        usage = self._calc_usage(messages, full_reply_content)
        self._update_costs(usage)
        return full_reply_content

    def _cons_kwargs(self, messages: list[dict]) -> dict:
        if CONFIG.openai_api_type == "azure":
            kwargs = {
                "deployment_id": CONFIG.deployment_id,
                "messages": messages,
                "max_tokens": self.get_max_tokens(messages),
                "n": 1,
                "stop": None,
                "temperature": 0.3,
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

    async def _achat_completion(self, messages: list[dict]) -> dict:
        rsp = await self.async_retry_call(self.llm.ChatCompletion.acreate, **self._cons_kwargs(messages))
        self._update_costs(rsp.get("usage"))
        return rsp

    def _chat_completion(self, messages: list[dict]) -> dict:
        rsp = self.retry_call(self.llm.ChatCompletion.create, **self._cons_kwargs(messages))
        self._update_costs(rsp)
        return rsp

    def completion(self, messages: list[dict]) -> dict:
        # if isinstance(messages[0], Message):
        #     messages = self.messages_to_dict(messages)
        return self._chat_completion(messages)

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
    async def acompletion_text(self, messages: list[dict], stream=False) -> str:
        """when streaming, print each token in place."""
        if stream:
            return await self._achat_completion_stream(messages)
        rsp = await self._achat_completion(messages)
        return self.get_choice_text(rsp)

    def _calc_usage(self, messages: list[dict], rsp: str) -> dict:
        usage = {}
        if CONFIG.calc_usage:
            try:
                prompt_tokens = count_message_tokens(messages, self.model)
                completion_tokens = count_string_tokens(rsp, self.model)
                usage["prompt_tokens"] = prompt_tokens
                usage["completion_tokens"] = completion_tokens
                return usage
            except Exception as e:
                logger.error("usage calculation failed!", e)
        else:
            return usage

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

    def _update_costs(self, usage: dict):
        if CONFIG.calc_usage:
            try:
                prompt_tokens = int(usage["prompt_tokens"])
                completion_tokens = int(usage["completion_tokens"])
                CONFIG.cost_manager.update_cost(prompt_tokens, completion_tokens, self.model)
            except Exception as e:
                logger.error("updating costs failed!", e)

    def get_costs(self) -> Costs:
        return CONFIG.cost_manager.get_costs()

    def get_max_tokens(self, messages: list[dict]):
        if not self.auto_max_tokens:
            return CONFIG.max_tokens_rsp
        return get_max_completion_tokens(messages, self.model, CONFIG.max_tokens_rsp)

    async def get_summary(self, text: str, max_words=200):
        max_token_count = DEFAULT_MAX_TOKENS
        max_count = 100
        while max_count > 0:
            if len(text) < max_token_count:
                return await self._get_summary(text, max_words=max_words)

            text_windows = self.split_texts(text, window_size=max_token_count - max_words)
            summaries = []
            for ws in text_windows:
                response = await self._get_summary(ws, max_words=max_words)
                summaries.append(response)
            if len(summaries) == 1:
                return summaries[0]

            # Merged and retry
            text = "\n".join(summaries)

            max_count -= 1  # safeguard
        raise openai.error.InvalidRequestError("text too long")

    async def _get_summary(self, text: str, max_words=20):
        """Generate text summary"""
        if len(text) < max_words:
            return text
        command = f"Translate the above content into a summary of less than {max_words} words."
        msg = text + "\n\n" + command
        logger.info(f"summary ask:{msg}")
        response = await self.aask(msg=msg, system_msgs=[])
        logger.info(f"summary rsp: {response}")
        return response

    async def get_context_title(self, text: str, max_words=5) -> str:
        """Generate text title"""
        summary = await self.get_summary(text, max_words)

        language = CONFIG.language or DEFAULT_LANGUAGE
        command = f"Translate the above summary into a {language} title of less than {max_words} words."
        summaries = [summary, command]
        msg = "\n".join(summaries)
        logger.info(f"title ask:{msg}")
        response = await self.aask(msg=msg, system_msgs=[])
        logger.info(f"title rsp: {response}")
        return response

    async def is_related(self, text1, text2):
        command = f"{text1}\n{text2}\n\nIf the two sentences above are related, return [TRUE] brief and clear. Otherwise, return [FALSE]."
        rsp = await self.aask(msg=command, system_msgs=[])
        result, _ = self.extract_info(rsp)
        return result == "TRUE"

    async def rewrite(self, sentence: str, context: str):
        command = (
            f"{context}\n\nConsidering the content above, rewrite and return this sentence brief and clear:\n{sentence}"
        )
        rsp = await self.aask(msg=command, system_msgs=[])
        return rsp

    @staticmethod
    def split_texts(text: str, window_size) -> List[str]:
        """Splitting long text into sliding windows text"""
        if window_size <= 0:
            window_size = OpenAIGPTAPI.DEFAULT_TOKEN_SIZE
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

    @staticmethod
    def extract_info(input_string):
        pattern = r"\[([A-Z]+)\]:\s*(.+)"
        match = re.match(pattern, input_string)
        if match:
            return match.group(1), match.group(2)
        else:
            return None, input_string

    @staticmethod
    async def async_retry_call(func, *args, **kwargs):
        for i in range(OpenAIGPTAPI.MAX_TRY):
            try:
                rsp = await func(*args, **kwargs)
                return rsp
            except openai.error.RateLimitError as e:
                random_time = random.uniform(0, 3)  # 生成0到5秒之间的随机时间
                rounded_time = round(random_time, 1)  # 保留一位小数，以实现0.1秒的精度
                logger.warning(f"Exception:{e}, sleeping for {rounded_time} seconds")
                await asyncio.sleep(rounded_time)
                continue
            except Exception as e:
                error_str = traceback.format_exc()
                logger.error(f"Exception:{e}, stack:{error_str}")
                raise e
        raise openai.error.OpenAIError("Exceeds the maximum retries")

    @staticmethod
    def retry_call(func, *args, **kwargs):
        for i in range(OpenAIGPTAPI.MAX_TRY):
            try:
                rsp = func(*args, **kwargs)
                return rsp
            except openai.error.RateLimitError as e:
                logger.warning(f"Exception:{e}")
                continue
            except (
                openai.error.AuthenticationError,
                openai.error.PermissionError,
                openai.error.InvalidAPIType,
                openai.error.SignatureVerificationError,
            ) as e:
                logger.warning(f"Exception:{e}")
                raise e
            except Exception as e:
                error_str = traceback.format_exc()
                logger.error(f"Exception:{e}, stack:{error_str}")
                raise e
        raise openai.error.OpenAIError("Exceeds the maximum retries")

    MAX_TRY = 5
    DEFAULT_TOKEN_SIZE = 500


if __name__ == "__main__":
    txt = """
as dfas  sad lkf sdkl sakdfsdk sjd jsk  sdl sk dd sd asd fa sdf sad dd
- .gitlab-ci.yml & base_test.py
    """
    OpenAIGPTAPI.split_texts(txt, 30)
