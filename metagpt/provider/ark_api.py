#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provider for volcengine.
See Also: https://console.volcengine.com/ark/region:ark+cn-beijing/model

config2.yaml example:
```yaml
llm:
  base_url: "https://ark.cn-beijing.volces.com/api/v3"
  api_type: "ark"
  endpoint: "ep-2024080514****-d****"
  api_key: "d47****b-****-****-****-d6e****0fd77"
  pricing_plan: "doubao-lite"
```
"""
from typing import Optional, Union

from pydantic import BaseModel
from volcenginesdkarkruntime import AsyncArk
from volcenginesdkarkruntime._base_client import AsyncHttpxClientWrapper
from volcenginesdkarkruntime._streaming import AsyncStream
from volcenginesdkarkruntime.types.chat import ChatCompletion, ChatCompletionChunk

from metagpt.configs.llm_config import LLMType
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.logs import log_llm_stream
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.provider.openai_api import OpenAILLM
from metagpt.utils.token_counter import DOUBAO_TOKEN_COSTS


@register_provider(LLMType.ARK)
class ArkLLM(OpenAILLM):
    """
    用于火山方舟的API
    见：https://www.volcengine.com/docs/82379/1263482
    """

    aclient: Optional[AsyncArk] = None

    def _init_client(self):
        """SDK: https://github.com/openai/openai-python#async-usage"""
        self.model = (
            self.config.endpoint or self.config.model
        )  # endpoint name, See more: https://console.volcengine.com/ark/region:ark+cn-beijing/endpoint
        self.pricing_plan = self.config.pricing_plan or self.model
        kwargs = self._make_client_kwargs()
        self.aclient = AsyncArk(**kwargs)

    def _make_client_kwargs(self) -> dict:
        kvs = {
            "ak": self.config.access_key,
            "sk": self.config.secret_key,
            "api_key": self.config.api_key,
            "base_url": self.config.base_url,
        }
        kwargs = {k: v for k, v in kvs.items() if v}

        # to use proxy, openai v1 needs http_client
        if proxy_params := self._get_proxy_params():
            kwargs["http_client"] = AsyncHttpxClientWrapper(**proxy_params)

        return kwargs

    def _update_costs(self, usage: Union[dict, BaseModel], model: str = None, local_calc_usage: bool = True):
        if next(iter(DOUBAO_TOKEN_COSTS)) not in self.cost_manager.token_costs:
            self.cost_manager.token_costs.update(DOUBAO_TOKEN_COSTS)
        if model in self.cost_manager.token_costs:
            self.pricing_plan = model
        if self.pricing_plan in self.cost_manager.token_costs:
            super()._update_costs(usage, self.pricing_plan, local_calc_usage)

    async def _achat_completion_stream(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> str:
        response: AsyncStream[ChatCompletionChunk] = await self.aclient.chat.completions.create(
            **self._cons_kwargs(messages, timeout=self.get_timeout(timeout)),
            stream=True,
            extra_body={"stream_options": {"include_usage": True}},  # 只有增加这个参数才会在流式时最后返回usage
        )
        usage = None
        collected_messages = []
        async for chunk in response:
            chunk_message = chunk.choices[0].delta.content or "" if chunk.choices else ""  # extract the message
            log_llm_stream(chunk_message)
            collected_messages.append(chunk_message)
            if chunk.usage:
                # 火山方舟的流式调用会在最后一个chunk中返回usage,最后一个chunk的choices为[]
                usage = chunk.usage

        log_llm_stream("\n")
        full_reply_content = "".join(collected_messages)
        self._update_costs(usage, chunk.model)
        return full_reply_content

    async def _achat_completion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> ChatCompletion:
        kwargs = self._cons_kwargs(messages, timeout=self.get_timeout(timeout))
        rsp: ChatCompletion = await self.aclient.chat.completions.create(**kwargs)
        self._update_costs(rsp.usage, rsp.model)
        return rsp
