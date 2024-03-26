#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : llm api of qianfan from Baidu, supports ERNIE(wen xin yi yan) and opensource models
import copy
import os

import qianfan
from qianfan import ChatCompletion
from qianfan.resources.typing import JsonBody

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.logs import log_llm_stream
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.utils.cost_manager import CostManager
from metagpt.utils.token_counter import (
    QIANFAN_ENDPOINT_TOKEN_COSTS,
    QIANFAN_MODEL_TOKEN_COSTS,
)


@register_provider(LLMType.QIANFAN)
class QianFanLLM(BaseLLM):
    """
    Refs
        Auth: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/3lmokh7n6#%E3%80%90%E6%8E%A8%E8%8D%90%E3%80%91%E4%BD%BF%E7%94%A8%E5%AE%89%E5%85%A8%E8%AE%A4%E8%AF%81aksk%E9%89%B4%E6%9D%83%E8%B0%83%E7%94%A8%E6%B5%81%E7%A8%8B
        Token Price: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/hlrk4akp7#tokens%E5%90%8E%E4%BB%98%E8%B4%B9
        Models: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/wlmhm7vuo#%E5%AF%B9%E8%AF%9Dchat
                https://cloud.baidu.com/doc/WENXINWORKSHOP/s/xlmokikxe#%E6%94%AF%E6%8C%81%E6%A8%A1%E5%9E%8B%E5%88%97%E8%A1%A8
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self.use_system_prompt = False  # only some ERNIE-x related models support system_prompt
        self.__init_qianfan()
        self.cost_manager = CostManager(token_costs=self.token_costs)

    def __init_qianfan(self):
        if self.config.access_key and self.config.secret_key:
            # for system level auth, use access_key and secret_key, recommended by official
            # set environment variable due to official recommendation
            os.environ.setdefault("QIANFAN_ACCESS_KEY", self.config.access_key)
            os.environ.setdefault("QIANFAN_SECRET_KEY", self.config.secret_key)
        elif self.config.api_key and self.config.secret_key:
            # for application level auth, use api_key and secret_key
            # set environment variable due to official recommendation
            os.environ.setdefault("QIANFAN_AK", self.config.api_key)
            os.environ.setdefault("QIANFAN_SK", self.config.secret_key)
        else:
            raise ValueError("Set the `access_key`&`secret_key` or `api_key`&`secret_key` first")

        support_system_pairs = [
            ("ERNIE-Bot-4", "completions_pro"),  # (model, corresponding-endpoint)
            ("ERNIE-Bot-8k", "ernie_bot_8k"),
            ("ERNIE-Bot", "completions"),
            ("ERNIE-Bot-turbo", "eb-instant"),
            ("ERNIE-Speed", "ernie_speed"),
            ("EB-turbo-AppBuilder", "ai_apaas"),
        ]
        if self.config.model in [pair[0] for pair in support_system_pairs]:
            # only some ERNIE models support
            self.use_system_prompt = True
        if self.config.endpoint in [pair[1] for pair in support_system_pairs]:
            self.use_system_prompt = True

        assert not (self.config.model and self.config.endpoint), "Only set `model` or `endpoint` in the config"
        assert self.config.model or self.config.endpoint, "Should set one of `model` or `endpoint` in the config"

        self.token_costs = copy.deepcopy(QIANFAN_MODEL_TOKEN_COSTS)
        self.token_costs.update(QIANFAN_ENDPOINT_TOKEN_COSTS)

        # self deployed model on the cloud not to calculate usage, it charges resource pool rental fee
        self.calc_usage = self.config.calc_usage and self.config.endpoint is None
        self.aclient: ChatCompletion = qianfan.ChatCompletion()

    def _const_kwargs(self, messages: list[dict], stream: bool = False) -> dict:
        kwargs = {
            "messages": messages,
            "stream": stream,
        }
        if self.config.temperature > 0:
            # different model has default temperature. only set when it's specified.
            kwargs["temperature"] = self.config.temperature
        if self.config.endpoint:
            kwargs["endpoint"] = self.config.endpoint
        elif self.config.model:
            kwargs["model"] = self.config.model

        if self.use_system_prompt:
            # if the model support system prompt, extract and pass it
            if messages[0]["role"] == "system":
                kwargs["messages"] = messages[1:]
                kwargs["system"] = messages[0]["content"]  # set system prompt here
        return kwargs

    def _update_costs(self, usage: dict):
        """update each request's token cost"""
        model_or_endpoint = self.config.model or self.config.endpoint
        local_calc_usage = model_or_endpoint in self.token_costs
        super()._update_costs(usage, model_or_endpoint, local_calc_usage)

    def get_choice_text(self, resp: JsonBody) -> str:
        return resp.get("result", "")

    def completion(self, messages: list[dict]) -> JsonBody:
        resp = self.aclient.do(**self._const_kwargs(messages=messages, stream=False))
        self._update_costs(resp.body.get("usage", {}))
        return resp.body

    async def _achat_completion(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> JsonBody:
        resp = await self.aclient.ado(**self._const_kwargs(messages=messages, stream=False))
        self._update_costs(resp.body.get("usage", {}))
        return resp.body

    async def acompletion(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> JsonBody:
        return await self._achat_completion(messages, timeout=self.get_timeout(timeout))

    async def _achat_completion_stream(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> str:
        resp = await self.aclient.ado(**self._const_kwargs(messages=messages, stream=True))
        collected_content = []
        usage = {}
        async for chunk in resp:
            content = chunk.body.get("result", "")
            usage = chunk.body.get("usage", {})
            log_llm_stream(content)
            collected_content.append(content)
        log_llm_stream("\n")

        self._update_costs(usage)
        full_content = "".join(collected_content)
        return full_content
