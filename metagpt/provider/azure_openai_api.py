# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/5 23:08
@Author  : alexanderwu
@File    : openai.py
@Modified By: mashenquan, 2023/8/20. Remove global configuration `CONFIG`, enable configuration support for business isolation;
            Change cost control from global to company level.
@Modified By: mashenquan, 2023/11/21. Fix bug: ReadTimeout.
@Modified By: mashenquan, 2023/12/1. Fix bug: Unclosed connection caused by openai 0.x.
"""


from openai import AsyncAzureOpenAI
from openai._base_client import AsyncHttpxClientWrapper

from metagpt.config import LLMProviderEnum
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.provider.openai_api import OpenAILLM


@register_provider(LLMProviderEnum.AZURE_OPENAI)
class AzureOpenAILLM(OpenAILLM):
    """
    Check https://platform.openai.com/examples for examples
    """

    def _init_client(self):
        kwargs = self._make_client_kwargs()
        # https://learn.microsoft.com/zh-cn/azure/ai-services/openai/how-to/migration?tabs=python-new%2Cdalle-fix
        self.aclient = AsyncAzureOpenAI(**kwargs)
        self.model = self.config.DEPLOYMENT_NAME  # Used in _calc_usage & _cons_kwargs

    def _make_client_kwargs(self) -> dict:
        kwargs = dict(
            api_key=self.config.OPENAI_API_KEY,
            api_version=self.config.OPENAI_API_VERSION,
            azure_endpoint=self.config.OPENAI_BASE_URL,
        )

        # to use proxy, openai v1 needs http_client
        proxy_params = self._get_proxy_params()
        if proxy_params:
            kwargs["http_client"] = AsyncHttpxClientWrapper(**proxy_params)

        return kwargs
