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
)
