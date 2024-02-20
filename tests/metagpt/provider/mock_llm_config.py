#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/8 17:03
@Author  : alexanderwu
@File    : mock_llm_config.py
"""

from metagpt.configs.llm_config import LLMConfig

mock_llm_config = LLMConfig(
    llm_type="mock",
    api_key="mock_api_key",
    base_url="mock_base_url",
    app_id="mock_app_id",
    api_secret="mock_api_secret",
    domain="mock_domain",
)


mock_llm_config_proxy = LLMConfig(
    llm_type="mock",
    api_key="mock_api_key",
    base_url="mock_base_url",
    proxy="http://localhost:8080",
)


mock_llm_config_azure = LLMConfig(
    llm_type="azure",
    api_version="2023-09-01-preview",
    api_key="mock_api_key",
    base_url="mock_base_url",
    proxy="http://localhost:8080",
)


mock_llm_config_zhipu = LLMConfig(
    llm_type="zhipu",
    api_key="mock_api_key.zhipu",
    base_url="mock_base_url",
    model="mock_zhipu_model",
    proxy="http://localhost:8080",
)

mock_llm_config_openailike = LLMConfig(
    api_type= "openai_like",
    base_url= "https://api.moonshot.cn/v1",
    api_key="mock_api_key.moonshot",
    model="moonshot-v1-8k"
)