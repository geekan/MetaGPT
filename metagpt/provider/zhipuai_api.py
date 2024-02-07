#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : zhipuai LLM from https://open.bigmodel.cn/dev/api#sdk

from enum import Enum
from typing import Optional

from requests import ConnectionError
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)
from zhipuai.types.chat.chat_completion import Completion

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.logs import log_llm_stream, logger
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.provider.openai_api import log_and_reraise
from metagpt.provider.zhipuai.zhipu_model_api import ZhiPuModelAPI
from metagpt.utils.cost_manager import CostManager


class ZhiPuEvent(Enum):
    ADD = "add"
    ERROR = "error"
    INTERRUPTED = "interrupted"
    FINISH = "finish"


@register_provider(LLMType.ZHIPUAI)
class ZhiPuAILLM(BaseLLM):
    """
    Refs to `https://open.bigmodel.cn/dev/api#chatglm_turbo`
    From now, support glm-3-turbo、glm-4, and also system_prompt.
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self.__init_zhipuai()
        self.cost_manager: Optional[CostManager] = None

    def __init_zhipuai(self):
        assert self.config.api_key
        self.api_key = self.config.api_key
        self.model = self.config.model  # so far, it support glm-3-turbo、glm-4
        self.llm = ZhiPuModelAPI(api_key=self.api_key)

    def _const_kwargs(self, messages: list[dict], stream: bool = False) -> dict:
        kwargs = {"model": self.model, "messages": messages, "stream": stream, "temperature": 0.3}
        return kwargs

    def _update_costs(self, usage: dict):
        """update each request's token cost"""
        if self.config.calc_usage:
            try:
                prompt_tokens = int(usage.get("prompt_tokens", 0))
                completion_tokens = int(usage.get("completion_tokens", 0))
                self.cost_manager.update_cost(prompt_tokens, completion_tokens, self.model)
            except Exception as e:
                logger.error(f"zhipuai updats costs failed! exp: {e}")

    def completion(self, messages: list[dict], timeout=3) -> dict:
        resp: Completion = self.llm.chat.completions.create(**self._const_kwargs(messages))
        usage = resp.usage.model_dump()
        self._update_costs(usage)
        return resp.model_dump()

    async def _achat_completion(self, messages: list[dict], timeout=3) -> dict:
        resp = await self.llm.acreate(**self._const_kwargs(messages))
        usage = resp.get("usage", {})
        self._update_costs(usage)
        return resp

    async def acompletion(self, messages: list[dict], timeout=3) -> dict:
        return await self._achat_completion(messages, timeout=timeout)

    async def _achat_completion_stream(self, messages: list[dict], timeout=3) -> str:
        response = await self.llm.acreate_stream(**self._const_kwargs(messages, stream=True))
        collected_content = []
        usage = {}
        async for chunk in response.stream():
            finish_reason = chunk.get("choices")[0].get("finish_reason")
            if finish_reason == "stop":
                usage = chunk.get("usage", {})
            else:
                content = self.get_choice_delta_text(chunk)
                collected_content.append(content)
                log_llm_stream(content)

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
    async def acompletion_text(self, messages: list[dict], stream=False, timeout=3) -> str:
        """response in async with stream or non-stream mode"""
        if stream:
            return await self._achat_completion_stream(messages)
        resp = await self._achat_completion(messages)
        return self.get_choice_text(resp)
