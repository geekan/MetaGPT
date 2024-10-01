import copy
import os
import requests
import json
import sys
import pdb
import json
import requests
import hashlib
import uuid
import time
import traceback
import re
from pathlib import Path
import pandas as pd
import datetime
import uuid
import qianfan
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

@register_provider(LLMType.SHAHE)
class OwnLLM(BaseLLM):
    """
    create your own api
    """
    def __init__(self, config: LLMConfig):
        self.config = config
        self.use_system_prompt = False  
        self.__init_ownapi()
        self.cost_manager = CostManager(token_costs=self.token_costs)


    def __init_ownapi(self):
        # finish your own init
        
    def _const_kwargs(self, messages: list[dict], stream: bool = False) -> dict:
        kwargs = {
            "messages": messages,
            "stream": stream,
        }
        if self.config.temperature > 0:
            kwargs["temperature"] = self.config.temperature
        if self.config.endpoint:
            kwargs["endpoint"] = self.config.endpoint
        elif self.config.model:
            kwargs["model"] = self.config.model

        if self.use_system_prompt:
            if messages[0]["role"] == "system":
                kwargs["messages"] = messages[1:]
                kwargs["system"] = messages[0]["content"]
        return kwargs

    def _update_costs(self, usage: dict):
        """update each request's token cost"""
        model_or_endpoint = self.config.model or self.config.endpoint
        local_calc_usage = model_or_endpoint in self.token_costs
        super()._update_costs(usage, model_or_endpoint, local_calc_usage)

    def get_choice_text(self, resp: JsonBody) -> str:
        return resp.get("result", "")

    def request_eb_dynamic_ppo(self, query, history, model_id="", compute_close=False):
        # here is the example
        
        URL = ""  
        payload = {
            "text": query,
            "model_version": "",
            "session_id": uuid.uuid1().hex,
            "history": history,
            "userId": "",
            "key":"",
            "model_id": model_id
        }
        headers = {
            'Content-Type': 'application/json'
        }
        resp_json = None
        for i in range(666):
            try:
                resp = requests.post(URL, headers=headers, data=json.dumps(payload))
                # print(query)
                # print(resp)
                resp_json = json.loads(resp.text)
                # print(resp_json)
                result = resp_json["data"]["result"]
                return resp_json
            except:
                # print(f"Fail to get EB result, try times: {i}")
                time.sleep(1)
                resp_json = None
        return resp_json

    def completion(self, messages: list[dict]) -> JsonBody:
        history = []
        for message in messages:
            query = message["content"]
            res = self.request_eb_dynamic_ppo(query, history, model_id="")
            result = res["data"]["result"]
            history.insert(0, [query, result])
        # Here we just return the final response, you can modify it to return all responses if needed
        return res

    async def _achat_completion(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> JsonBody:
        return self.completion(messages)

    async def acompletion(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> JsonBody:
        return await self._achat_completion(messages, timeout=self.get_timeout(timeout))

    async def _achat_completion_stream(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> str:
        collected_content = []
        history = []
        for message in messages:
            query = message["content"]
            res = self.request_eb_dynamic_ppo(query, history, model_id="")
            content = res["data"]["result"]
            log_llm_stream(content)
            collected_content.append(content)
            log_llm_stream("\n")
            history.insert(0, [query, content])
        full_content = "".join(collected_content)
        return full_content