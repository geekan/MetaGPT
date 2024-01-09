#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/13 12:29
@Author  : femto Zheng
@File    : make_sk_kernel.py
"""
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import (
    AzureChatCompletion,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import (
    OpenAIChatCompletion,
)

from metagpt.config2 import config


def make_sk_kernel():
    kernel = sk.Kernel()
    if llm := config.get_azure_llm():
        kernel.add_chat_service(
            "chat_completion",
            AzureChatCompletion(llm.model, llm.base_url, llm.api_key),
        )
    elif llm := config.get_openai_llm():
        kernel.add_chat_service(
            "chat_completion",
            OpenAIChatCompletion(llm.model, llm.api_key),
        )

    return kernel
