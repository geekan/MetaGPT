#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/9 15:57
@Author  : alexanderwu
@File    : test_config.py
"""

from metagpt.config2 import Config, config
from metagpt.configs.llm_config import LLMType


def test_config_1():
    cfg = Config.default()
    llm = cfg.get_openai_llm()
    assert llm is not None
    assert llm.api_type == LLMType.OPENAI


def test_config_2():
    assert config == Config.default()
