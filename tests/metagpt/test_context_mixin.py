#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/11 19:24
@Author  : alexanderwu
@File    : test_context_mixin.py
"""
from pathlib import Path

import pytest
from pydantic import BaseModel

from metagpt.actions import Action
from metagpt.config2 import Config
from metagpt.const import CONFIG_ROOT
from metagpt.context_mixin import ContextMixin
from metagpt.environment import Environment
from metagpt.roles import Role
from metagpt.team import Team
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
    assert obj.config.llm.model == "mock_zhipu_model"


@pytest.mark.asyncio
async def test_config_priority():
    """If action's config is set, then its llm will be set, otherwise, it will use the role's llm"""
    home_dir = Path.home() / CONFIG_ROOT
    gpt4t = Config.from_home("gpt-4-1106-preview.yaml")
    if not home_dir.exists():
        assert gpt4t is None
    gpt35 = Config.default()
    gpt35.llm.model = "gpt-3.5-turbo-1106"
    gpt4 = Config.default()
    gpt4.llm.model = "gpt-4-0613"

    a1 = Action(config=gpt4t, name="Say", instruction="Say your opinion with emotion and don't repeat it")
    a2 = Action(name="Say", instruction="Say your opinion with emotion and don't repeat it")
    a3 = Action(name="Vote", instruction="Vote for the candidate, and say why you vote for him/her")

    # it will not work for a1 because the config is already set
    A = Role(name="A", profile="Democratic candidate", goal="Win the election", actions=[a1], watch=[a2], config=gpt4)
    # it will work for a2 because the config is not set
    B = Role(name="B", profile="Republican candidate", goal="Win the election", actions=[a2], watch=[a1], config=gpt4)
    # ditto
    C = Role(name="C", profile="Voter", goal="Vote for the candidate", actions=[a3], watch=[a1, a2], config=gpt35)

    env = Environment(desc="US election live broadcast")
    Team(investment=10.0, env=env, roles=[A, B, C])

    assert a1.llm.model == "gpt-4-1106-preview" if Path(home_dir / "gpt-4-1106-preview.yaml").exists() else "gpt-4-0613"
    assert a2.llm.model == "gpt-4-0613"
    assert a3.llm.model == "gpt-3.5-turbo-1106"

    # history = await team.run(idea="Topic: climate change. Under 80 words per message.", send_to="a1", n_round=3)
