#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/9 15:57
@Author  : alexanderwu
@File    : test_config.py
"""

from metagpt.config2 import Config, config
from metagpt.configs.llm_config import LLMType
from tests.metagpt.provider.mock_llm_config import mock_llm_config


def test_config_1():
    cfg = Config.default()
    llm = cfg.get_openai_llm()
    assert llm is not None
    assert llm.api_type == LLMType.OPENAI


def test_config_2():
    assert config == Config.default()


def test_config_from_dict():
    cfg = Config(llm={"default": mock_llm_config})
    assert cfg
    assert cfg.llm["default"].api_key == "mock_api_key"
