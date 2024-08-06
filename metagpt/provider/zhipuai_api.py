#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : zhipuai LLM from https://open.bigmodel.cn/dev/api#sdk

from enum import Enum
from typing import Optional

from zhipuai.types.chat.chat_completion import Completion

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.logs import log_llm_stream
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.llm_provider_registry import register_provider
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
        self.pricing_plan = self.config.pricing_plan or self.model
        self.llm = ZhiPuModelAPI(api_key=self.api_key)

    def _const_kwargs(self, messages: list[dict], stream: bool = False) -> dict:
        max_tokens = self.config.max_token if self.config.max_token > 0 else 1024
        temperature = self.config.temperature if self.config.temperature > 0.0 else 0.3
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
            "stream": stream,
            "temperature": temperature,
        }
        return kwargs

    def completion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> dict:
        resp: Completion = self.llm.chat.completions.create(**self._const_kwargs(messages))
        usage = resp.usage.model_dump()
        self._update_costs(usage)
        return resp.model_dump()

    async def _achat_completion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> dict:
        resp = await self.llm.acreate(**self._const_kwargs(messages))
        usage = resp.get("usage", {})
        self._update_costs(usage)
        return resp

    async def acompletion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> dict:
        return await self._achat_completion(messages, timeout=self.get_timeout(timeout))

    async def _achat_completion_stream(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> str:
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
