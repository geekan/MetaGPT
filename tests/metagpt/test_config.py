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


class ModelX(ConfigMixin, BaseModel):
    a: str = "a"
    b: str = "b"


class WTFMixin(BaseModel):
    c: str = "c"
    d: str = "d"

    def __init__(self, **data):
        super().__init__(**data)


class ModelY(WTFMixin, ModelX):
    def __init__(self, **data):
        super().__init__(**data)


def test_config_mixin_1():
    new_model = ModelX()
    assert new_model.a == "a"
    assert new_model.b == "b"


def test_config_mixin_2():
    i = Config(llm={"default": mock_llm_config})
    j = Config(llm={"new": mock_llm_config})
    obj = ModelX(config=i)
    assert obj.config == i
    assert obj.config.llm["default"] == mock_llm_config

    obj.set_config(j)
    # obj already has a config, so it will not be set
    assert obj.config == i


def test_config_mixin_3():
    """Test config mixin with multiple inheritance"""
    i = Config(llm={"default": mock_llm_config})
    j = Config(llm={"new": mock_llm_config})
    obj = ModelY(config=i)
    assert obj.config == i
    assert obj.config.llm["default"] == mock_llm_config

    obj.set_config(j)
    # obj already has a config, so it will not be set
    assert obj.config == i
    assert obj.config.llm["default"] == mock_llm_config

    assert obj.a == "a"
    assert obj.b == "b"
    assert obj.c == "c"
    assert obj.d == "d"
