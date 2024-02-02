# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/5 23:08
@Author  : alexanderwu
@File    : openai.py
@Modified By: mashenquan, 2023/11/21. Fix bug: ReadTimeout.
@Modified By: mashenquan, 2023/12/1. Fix bug: Unclosed connection caused by openai 0.x.
"""
from openai import AsyncAzureOpenAI
from openai._base_client import AsyncHttpxClientWrapper
from openai.types import CompletionUsage

from metagpt.configs.llm_config import LLMType
from metagpt.logs import logger
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.provider.openai_api import OpenAILLM
from metagpt.utils import TOKEN_COSTS, count_message_tokens, count_string_tokens
from metagpt.utils.exceptions import handle_exception


@register_provider(LLMType.AZURE)
class AzureOpenAILLM(OpenAILLM):
    """
    Check https://platform.openai.com/examples for examples
    """

    def _init_client(self):
        kwargs = self._make_client_kwargs()
        # https://learn.microsoft.com/zh-cn/azure/ai-services/openai/how-to/migration?tabs=python-new%2Cdalle-fix
        self.aclient = AsyncAzureOpenAI(**kwargs)
        self.model = self.config.model  # Used in _calc_usage & _cons_kwargs

    def _make_client_kwargs(self) -> dict:
        kwargs = dict(
            api_key=self.config.api_key,
            api_version=self.config.api_version,
            azure_endpoint=self.config.base_url,
        )

        # to use proxy, openai v1 needs http_client
        proxy_params = self._get_proxy_params()
        if proxy_params:
            kwargs["http_client"] = AsyncHttpxClientWrapper(**proxy_params)

        return kwargs

    def _calc_usage(self, messages: list[dict], rsp: str) -> CompletionUsage:
        usage = CompletionUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        if not self.config.calc_usage:
            return usage

        model_name = "gpt-35-turbo" if "gpt-3" in self.model.lower() else "gpt-4-turbo-preview"
        try:
            usage.prompt_tokens = count_message_tokens(messages, model_name)
            usage.completion_tokens = count_string_tokens(rsp, model_name)
        except Exception as e:
            logger.error(f"usage calculation failed: {e}")

        return usage

    @handle_exception
    def _update_costs(self, usage: CompletionUsage):
        if self.config.calc_usage and usage and self.cost_manager:
            model_name = self._get_azure_model()
            # More about pricing: https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/
            self.cost_manager.update_cost(usage.prompt_tokens, usage.completion_tokens, model_name)

    def _get_azure_model(self) -> str:
        models = [i.lower() for i in TOKEN_COSTS.keys() if "azure" in i]
        mappings = {i: set(i.split("-")) for i in models}
        words = self.model.lower().split("-")
        weights = []
        for k, v in mappings.items():
            count = 0
            for i in words:
                if i in v:
                    count += 1
            weights.append((k, count))
        sorted_list = sorted(weights, key=lambda x: x[1], reverse=True)
        return sorted_list[0][0]
