# -*- coding: utf-8 -*-
import json
import types

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.hunyuan.v20230901.hunyuan_client import HunyuanClient
from tencentcloud.hunyuan.v20230901.models import (
    ChatCompletionsRequest,
    ChatCompletionsResponse,
)

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.logs import log_llm_stream
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.utils.cost_manager import CostManager
from metagpt.utils.token_counter import HUNYUAN_MODEL_TOKEN_COSTS


@register_provider(LLMType.HUNYUAN)
class HunYuanLLM(BaseLLM):
    """参考资料
    腾讯混元大模型产品概述：https://cloud.tencent.com/document/product/1729/104753
    腾讯混元API接口说明：https://cloud.tencent.com/document/api/1729/105701
    腾讯混元Python SDK源码：https://github.com/TencentCloud/tencentcloud-sdk-python/blob/master/tencentcloud/hunyuan/v20230901/models.py
    腾讯云控制台API密钥管理：https://console.cloud.tencent.com/cam/capi
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self.secret_id = self.config.secret_id
        self.secret_key = self.config.secret_key
        self.endpoint = self.config.endpoint
        self.model = self.config.model
        self.region = ""
        self._init_client()
        self.cost_manager = CostManager(token_costs=HUNYUAN_MODEL_TOKEN_COSTS)

    def _init_client(self):
        """实例化一个认证客户端对象"""
        cred = credential.Credential(self.secret_id, self.secret_key)
        httpProfile = HttpProfile()
        httpProfile.endpoint = self.endpoint
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        self.aclient: HunyuanClient = HunyuanClient(cred, self.region, clientProfile)

    def _format_messages(self, messages: list[dict]) -> list[dict]:
        """将role和content转换为Role和Content"""
        new_messages = []
        for message in messages:
            new_messages.append({"Role": message["role"], "Content": message["content"]})
        return new_messages

    def _make_request(
        self,
        messages: list[dict],
        stream=True,
    ):
        """构造请求参数对象"""
        req = ChatCompletionsRequest()
        params = {
            "Model": self.model,
            "Messages": self._format_messages(messages),
            "Stream": stream,
        }
        req.from_json_string(json.dumps(params))
        return req

    async def _achat_completion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> ChatCompletionsResponse:
        resp: ChatCompletionsResponse = self.aclient.ChatCompletions(
            self._make_request(messages, timeout, stream=False)
        )
        # 转换为字典格式
        usage = {
            "prompt_tokens": resp.Usage.PromptTokens,
            "completion_tokens": resp.Usage.CompletionTokens,
        }
        self._update_costs(usage)
        return resp

    async def acompletion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> ChatCompletionsResponse:
        return await self._achat_completion(messages, timeout)

    async def _achat_completion_stream(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> str:
        resp = self.aclient.ChatCompletions(self._make_request(messages, timeout, stream=True))
        full_reply_content = ""
        usage = {}
        if isinstance(resp, types.GeneratorType):  # 流式响应
            for event in resp:
                data = json.loads(event["data"])
                usage = data.get("Usage", {})
                for choice in data["Choices"]:
                    content = choice["Delta"]["Content"]
                    log_llm_stream(content)
                    full_reply_content += content
        self._update_costs(
            {
                "prompt_tokens": usage.get("PromptTokens", 0),
                "completion_tokens": usage.get("CompletionTokens", 0),
            }
        )
        log_llm_stream("\n")
        return full_reply_content
