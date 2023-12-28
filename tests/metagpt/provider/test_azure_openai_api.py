#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/28
@Author  : mashenquan
@File    : test_azure_openai.py
"""
from metagpt.config import CONFIG, LLMProviderEnum
from metagpt.llm import LLM


def test_llm():
    # Prerequisites
    assert CONFIG.DEPLOYMENT_NAME and CONFIG.DEPLOYMENT_NAME != "YOUR_DEPLOYMENT_NAME"
    assert CONFIG.OPENAI_API_KEY and CONFIG.OPENAI_API_KEY != "YOUR_AZURE_API_KEY"
    assert CONFIG.OPENAI_API_VERSION
    assert CONFIG.OPENAI_BASE_URL

    llm = LLM(provider=LLMProviderEnum.AZURE_OPENAI)
    assert llm
