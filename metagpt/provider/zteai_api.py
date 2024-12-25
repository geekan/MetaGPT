import json
from typing import Optional, Union

import aiohttp

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.const import LLM_API_TIMEOUT, USE_CONFIG_TIMEOUT
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.llm_provider_registry import register_provider


async def ZTEAI(querytext, appid, apikey, numb, token, modeltype):
    url = "https://rdcloud.zte.com.cn/zte-studio-ai-platform/openapi/v1/chat"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + appid + "-" + apikey,
        "X-Emp-No": numb,
        "X-Auth-Value": token,
    }
    data = {"chatUuid": "", "chatName": "", "stream": False, "keep": True, "text": querytext, "model": modeltype}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            nowresult = await response.text()
            return json.loads(nowresult)["bo"]["result"]


@register_provider(LLMType.ZTEAI)
class ZTEaiLLM(BaseLLM):
    def __init__(self, config: LLMConfig):
        self.config = config

    async def ask(self, msg: str, timeout=USE_CONFIG_TIMEOUT) -> str:
        rsp = await ZTEAI(
            msg, self.config.app_id, self.config.api_key, self.config.domain, self.config.access_key, self.config.model
        )
        return rsp

    async def aask(
        self,
        msg: str,
        system_msgs: Optional[list[str]] = None,
        format_msgs: Optional[list[dict[str, str]]] = None,
        images: Optional[Union[str, list[str]]] = None,
        timeout=USE_CONFIG_TIMEOUT,
    ) -> str:
        return await self.ask(msg, timeout=self.get_timeout(timeout))

    async def _achat_completion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT):
        pass

    async def acompletion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT):
        """dummy implementation of abstract method in base"""
        return []

    async def _achat_completion_stream(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> str:
        pass

    async def acompletion_text(self, messages: list[dict], stream=False, timeout=USE_CONFIG_TIMEOUT) -> str:
        """dummy implementation of abstract method in base"""
        return ""

    def get_timeout(self, timeout: int) -> int:
        return timeout or LLM_API_TIMEOUT
