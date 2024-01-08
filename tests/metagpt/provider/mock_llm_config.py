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
