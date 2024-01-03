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

from metagpt.config import CONFIG


def make_sk_kernel():
    kernel = sk.Kernel()
    if CONFIG.OPENAI_API_TYPE == "azure":
        kernel.add_chat_service(
            "chat_completion",
            AzureChatCompletion(CONFIG.DEPLOYMENT_NAME, CONFIG.OPENAI_BASE_URL, CONFIG.OPENAI_API_KEY),
        )
    else:
        kernel.add_chat_service(
            "chat_completion",
            OpenAIChatCompletion(CONFIG.OPENAI_API_MODEL, CONFIG.OPENAI_API_KEY),
        )

    return kernel
