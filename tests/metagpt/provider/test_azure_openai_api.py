#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :


from metagpt.config import CONFIG
from metagpt.provider.azure_openai_api import AzureOpenAILLM

CONFIG.OPENAI_API_VERSION = "xx"
CONFIG.openai_proxy = "http://127.0.0.1:80"  # fake value


def test_azure_openai_api():
    _ = AzureOpenAILLM()
