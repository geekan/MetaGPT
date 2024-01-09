#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/9 15:57
@Author  : alexanderwu
@File    : test_config.py
"""
from pydantic import BaseModel

from metagpt.config2 import Config, ConfigMixin, config
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


class NewModel(ConfigMixin, BaseModel):
    a: str = "a"
    b: str = "b"


def test_config_mixin():
    new_model = NewModel()
    assert new_model.a == "a"
    assert new_model.b == "b"
    assert new_model._config == new_model.config
    assert new_model._config is None


def test_config_mixin_2():
    i = Config(llm={"default": mock_llm_config})
    new_model = NewModel(config=i)
    assert new_model.config == i
    assert new_model._config == i
    assert new_model.config.llm["default"] == mock_llm_config
