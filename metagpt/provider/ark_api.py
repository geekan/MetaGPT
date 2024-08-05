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

from metagpt.configs.llm_config import LLMType
from metagpt.provider import OpenAILLM
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.utils.token_counter import DOUBAO_TOKEN_COSTS


@register_provider(LLMType.ARK)
class ArkLLM(OpenAILLM):
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
        if self.pricing_plan in self.cost_manager.token_costs:
            super()._update_costs(usage, self.pricing_plan, local_calc_usage)
