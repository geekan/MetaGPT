#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/9 15:57
@Author  : alexanderwu
@File    : test_config.py
"""
from pydantic import BaseModel

from metagpt.config2 import Config
from metagpt.configs.llm_config import LLMType
from metagpt.context import ContextMixin
from tests.metagpt.provider.mock_llm_config import (
    mock_llm_config,
    mock_llm_config_proxy,
)


def test_config_1():
    cfg = Config.default()
    llm = cfg.get_openai_llm()
    assert llm is not None
    assert llm.api_type == LLMType.OPENAI


def test_config_from_dict():
    cfg = Config(llm=mock_llm_config)
    assert cfg
    assert cfg.llm.api_key == "mock_api_key"


class ModelX(ContextMixin, BaseModel):
    a: str = "a"
    b: str = "b"


class WTFMixin(BaseModel):
    c: str = "c"
    d: str = "d"


class ModelY(WTFMixin, ModelX):
    pass


def test_config_mixin_1():
    new_model = ModelX()
    assert new_model.a == "a"
    assert new_model.b == "b"


def test_config_mixin_2():
    i = Config(llm=mock_llm_config)
    j = Config(llm=mock_llm_config_proxy)
    obj = ModelX(config=i)
    assert obj._config == i
    assert obj._config.llm == mock_llm_config

    obj.set_config(j)
    # obj already has a config, so it will not be set
    assert obj._config == i


def test_config_mixin_3():
    """Test config mixin with multiple inheritance"""
    i = Config(llm=mock_llm_config)
    j = Config(llm=mock_llm_config_proxy)
    obj = ModelY(config=i)
    assert obj._config == i
    assert obj._config.llm == mock_llm_config

    obj.set_config(j)
    # obj already has a config, so it will not be set
    assert obj._config == i
    assert obj._config.llm == mock_llm_config

    assert obj.a == "a"
    assert obj.b == "b"
    assert obj.c == "c"
    assert obj.d == "d"

    print(obj.__dict__.keys())
    assert "_config" in obj.__dict__.keys()
