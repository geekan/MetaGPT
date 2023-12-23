#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/23 15:49
@Author  : alexanderwu
@File    : test_action_node.py
"""
import pytest

from metagpt.actions import Action
from metagpt.actions.action_node import ActionNode
from metagpt.environment import Environment
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team


@pytest.mark.asyncio
async def test_debate_two_roles():
    action1 = Action(name="BidenSay", instruction="Express opinions and argue vigorously, and strive to gain votes")
    action2 = Action(name="TrumpSay", instruction="Express opinions and argue vigorously, and strive to gain votes")
    biden = Role(
        name="Biden", profile="Democratic candidate", goal="Win the election", actions=[action1], watch=[action2]
    )
    trump = Role(
        name="Trump", profile="Republican candidate", goal="Win the election", actions=[action2], watch=[action1]
    )
    env = Environment(desc="US election live broadcast")
    team = Team(investment=10.0, env=env, roles=[biden, trump])

    history = await team.run(idea="Topic: climate change. Under 80 words per message.", send_to="Biden", n_round=3)
    assert "BidenSay" in history


@pytest.mark.asyncio
async def test_debate_one_role_in_env():
    action = Action(name="Debate", instruction="Express opinions and argue vigorously, and strive to gain votes")
    biden = Role(name="Biden", profile="Democratic candidate", goal="Win the election", actions=[action])
    env = Environment(desc="US election live broadcast")
    team = Team(investment=10.0, env=env, roles=[biden])
    history = await team.run(idea="Topic: climate change. Under 80 words per message.", send_to="Biden", n_round=3)
    assert "Debate" in history


@pytest.mark.asyncio
async def test_debate_one_role():
    action = Action(name="Debate", instruction="Express opinions and argue vigorously, and strive to gain votes")
    biden = Role(name="Biden", profile="Democratic candidate", goal="Win the election", actions=[action])
    msg: Message = await biden.run("Topic: climate change. Under 80 words per message.")

    assert len(msg.content) > 10
    assert msg.sent_from == "metagpt.roles.role.Role"


@pytest.mark.asyncio
async def test_action_node():
    node = ActionNode(key="key-a", expected_type=str, instruction="instruction-b", example="example-c")

    raw_template = node.compile(context="123", schema="raw", mode="auto")
    json_template = node.compile(context="123", schema="json", mode="auto")
    markdown_template = node.compile(context="123", schema="markdown", mode="auto")
    node_dict = node.to_dict()

    assert "123" in raw_template
    assert "instruction" in raw_template

    assert "123" in json_template
    assert "format example" in json_template
    assert "constraint" in json_template
    assert "action" in json_template
    assert "[/" in json_template

    assert "123" in markdown_template
    assert "key-a" in markdown_template

    assert node_dict["key-a"] == "instruction-b"
