#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/11 19:24
@Author  : alexanderwu
@File    : test_context_mixin.py
"""
import pytest
from pydantic import BaseModel

from metagpt.actions import Action
from metagpt.config2 import Config
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
    assert obj.llm.model == "mock_zhipu_model"


@pytest.mark.asyncio
async def test_debate_two_roles():
    config = Config.default()
    config.llm.model = "gpt-4-1106-preview"
    action1 = Action(config=config, name="AlexSay", instruction="Say your opinion with emotion and don't repeat it")
    action2 = Action(name="BobSay", instruction="Say your opinion with emotion and don't repeat it")
    alex = Role(
        name="Alex", profile="Democratic candidate", goal="Win the election", actions=[action1], watch=[action2]
    )
    bob = Role(name="Bob", profile="Republican candidate", goal="Win the election", actions=[action2], watch=[action1])
    env = Environment(desc="US election live broadcast")
    team = Team(investment=10.0, env=env, roles=[alex, bob])

    history = await team.run(idea="Topic: climate change. Under 80 words per message.", send_to="Alex", n_round=3)
    assert "Alex" in history
