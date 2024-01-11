#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/11 19:24
@Author  : alexanderwu
@File    : test_context_mixin.py
"""
from pydantic import BaseModel

from metagpt.config2 import Config
from metagpt.context_mixin import ContextMixin
from tests.metagpt.provider.mock_llm_config import (
    mock_llm_config,
    mock_llm_config_proxy,
    mock_llm_config_zhipu,
)


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
    assert obj.config == i
    assert obj.config.llm == mock_llm_config

    obj.set_config(j)
    # obj already has a config, so it will not be set
    assert obj.config == i


def test_config_mixin_3_multi_inheritance_not_override_config():
    """Test config mixin with multiple inheritance"""
    i = Config(llm=mock_llm_config)
    j = Config(llm=mock_llm_config_proxy)
    obj = ModelY(config=i)
    assert obj.config == i
    assert obj.config.llm == mock_llm_config

    obj.set_config(j)
    # obj already has a config, so it will not be set
    assert obj.config == i
    assert obj.config.llm == mock_llm_config

    assert obj.a == "a"
    assert obj.b == "b"
    assert obj.c == "c"
    assert obj.d == "d"

    print(obj.__dict__.keys())
    assert "private_config" in obj.__dict__.keys()


def test_config_mixin_4_multi_inheritance_override_config():
    """Test config mixin with multiple inheritance"""
    i = Config(llm=mock_llm_config)
    j = Config(llm=mock_llm_config_zhipu)
    obj = ModelY(config=i)
    assert obj.config == i
    assert obj.config.llm == mock_llm_config

    obj.set_config(j, override=True)
    # override obj.config
    assert obj.config == j
    assert obj.config.llm == mock_llm_config_zhipu

    assert obj.a == "a"
    assert obj.b == "b"
    assert obj.c == "c"
    assert obj.d == "d"

    print(obj.__dict__.keys())
    assert "private_config" in obj.__dict__.keys()
    assert obj.llm.model == "mock_zhipu_model"
