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
        self.__init_eb(config)
        self.client = GeneralAPIRequestor(base_url=config.eb_base_url)
        self.config = config
        self.suffix_url = "/chat/new"
        self.http_method = "post"

    def __init_eb(self, config: LLMConfig):
        assert config.eb_base_url, "ernie base url is required!"
        self.model_id = config.eb_model_id
        self.user_id = config.eb_user_id
        self.temperature = config.eb_temperature

    def get_payload_for_eb(self, messages, reminder, session_id):
        prompt = messages[-1]["content"]
        history = []
        for i in range(len(messages) - 1, -1, -2):
            if messages[i]['role'] == 'assistant':
                answer = messages[i]['content']
                if i - 1 >= 0 and messages[i - 1]['role'] == 'user':
                    question = messages[i - 1]['content']
                    history.append([question, answer])
        if session_id is None:
            random_int = random.randint(0, 2**31-1)
            session_id = f"{reminder}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random_int}"
        payload = {
            "session_id": session_id,
            "text": prompt,
            "eb_version": "main",
            "eda_version": "main",
            "model_id": self.model_id,
            "userId": self.user_id,
            "safe_close": False,
            "prompt_version": "V3",
            "temperature": self.temperature,
            "history": history
        }
        return payload

    def get_choice_text(self, resp: dict) -> str:
        return resp

    def get_usage(self, resp: dict) -> dict:
        return {"prompt_tokens": resp.get("prompt_eval_count", 0), "completion_tokens": resp.get("eval_count", 0)}

    def _decode_and_load(self, chunk: bytes, encoding: str = "utf-8") -> dict:
        chunk = chunk.decode(encoding)
        return json.loads(chunk)

    async def _achat_completion(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> dict:
        if messages[0]['role'] == 'system':
            system_prompt = messages[0]['content']
            messages = messages[1:]
            messages[0]['content'] = system_prompt + messages[0]['content']
        assert len(messages) % 2 == 1 and messages[-1]["role"] == "user"

        payload = self.get_payload_for_eb(messages, reminder=None, session_id=None)
        success = False
        request_time = 1
        resp = None
        while not success and request_time <= 5:
            try:
                resp, _, _ = await self.client.arequest(
                    method=self.http_method,
                    url=self.suffix_url,
                    params=payload,
                    request_timeout=self.get_timeout(timeout),
                )
                resp = self._decode_and_load(resp)
                if resp["msg"] == "success":
                    success = True
                    usage = self.get_usage(resp)
                    self._update_costs(usage)
                    resp = resp["data"]["result"]
                else:
                    request_time += 1
                time.sleep(1)
            except Exception as error:
                print(f"抓取失败，正在重试{request_time}/{5}，错误信息：{error}")
                request_time += 1
            time.sleep(1)
        return resp if success else None

    async def acompletion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> dict:
        return await self._achat_completion(messages, timeout=self.get_timeout(timeout))

    async def _achat_completion_stream(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> str:
        raise NotImplementedError()
