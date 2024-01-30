#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/9 13:52
@Author  : alexanderwu
@File    : test_context.py
"""
from metagpt.configs.llm_config import LLMType
from metagpt.context import AttrDict, Context


def test_attr_dict_1():
    ad = AttrDict(name="John", age=30)
    assert ad.name == "John"
    assert ad.age == 30
    assert ad.height is None


def test_attr_dict_2():
    ad = AttrDict(name="John", age=30)
    ad.height = 180
    assert ad.height == 180


def test_attr_dict_3():
    ad = AttrDict(name="John", age=30)
    del ad.age
    assert ad.age is None


def test_attr_dict_4():
    ad = AttrDict(name="John", age=30)
    try:
        del ad.weight
    except AttributeError as e:
        assert str(e) == "No such attribute: weight"


def test_attr_dict_5():
    ad = AttrDict.model_validate({"name": "John", "age": 30})
    assert ad.name == "John"
    assert ad.age == 30


def test_context_1():
    ctx = Context()
    assert ctx.config is not None
    assert ctx.git_repo is None
    assert ctx.src_workspace is None
    assert ctx.cost_manager is not None


def test_context_2():
    ctx = Context()
    llm = ctx.config.get_openai_llm()
    assert llm is not None
    assert llm.api_type == LLMType.OPENAI

    kwargs = ctx.kwargs
    assert kwargs is not None

    kwargs.test_key = "test_value"
    assert kwargs.test_key == "test_value"


def test_context_3():
    # ctx = Context()
    # ctx.use_llm(provider=LLMType.OPENAI)
    # assert ctx._llm_config is not None
    # assert ctx._llm_config.api_type == LLMType.OPENAI
    # assert ctx.llm() is not None
    # assert "gpt" in ctx.llm().model
    pass
