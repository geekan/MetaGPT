#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:44
@Author  : alexanderwu
@File    : test_role.py
@Modified By: mashenquan, 2023-11-1. In line with Chapter 2.2.1 and 2.2.2 of RFC 116, introduce unit tests for
            the utilization of the new message distribution feature in message handling.
@Modified By: mashenquan, 2023-11-4. According to the routing feature plan in Chapter 2.2.3.2 of RFC 113, the routing
    functionality is to be consolidated into the `Environment` class.
"""
import uuid

import pytest
from pydantic import BaseModel

from metagpt.actions import Action, ActionOutput, UserRequirement
from metagpt.environment import Environment
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.utils.common import any_to_str, get_class_name


class MockAction(Action):
    async def run(self, messages, *args, **kwargs):
        assert messages
        return ActionOutput(content=messages[-1].content, instruct_content=messages[-1])


class MockRole(Role):
    def __init__(self, name="", profile="", goal="", constraints="", desc=""):
        super().__init__(name=name, profile=profile, goal=goal, constraints=constraints, desc=desc)
        self._init_actions([MockAction()])


@pytest.mark.asyncio
async def test_react():
    class Input(BaseModel):
        name: str
        profile: str
        goal: str
        constraints: str
        desc: str
        subscription: str

    inputs = [
        {
            "name": "A",
            "profile": "Tester",
            "goal": "Test",
            "constraints": "constraints",
            "desc": "desc",
            "subscription": "start",
        }
    ]

    for i in inputs:
        seed = Input(**i)
        role = MockRole(
            name=seed.name, profile=seed.profile, goal=seed.goal, constraints=seed.constraints, desc=seed.desc
        )
        role.subscribe({seed.subscription})
        assert role._rc.watch == {any_to_str(UserRequirement)}
        assert role.name == seed.name
        assert role.profile == seed.profile
        assert role._setting.goal == seed.goal
        assert role._setting.constraints == seed.constraints
        assert role._setting.desc == seed.desc
        assert role.is_idle
        env = Environment()
        env.add_role(role)
        assert env.get_subscription(role) == {seed.subscription}
        env.publish_message(Message(content="test", msg_to=seed.subscription))
        assert not role.is_idle
        while not env.is_idle:
            await env.run()
        assert role.is_idle
        env.publish_message(Message(content="test", cause_by=seed.subscription))
        assert not role.is_idle
        while not env.is_idle:
            await env.run()
        assert role.is_idle
        tag = uuid.uuid4().hex
        role.subscribe({tag})
        assert env.get_subscription(role) == {tag}


@pytest.mark.asyncio
async def test_msg_to():
    m = Message(content="a", send_to=["a", MockRole, Message])
    assert m.send_to == set({"a", get_class_name(MockRole), get_class_name(Message)})

    m = Message(content="a", cause_by=MockAction, send_to={"a", MockRole, Message})
    assert m.send_to == set({"a", get_class_name(MockRole), get_class_name(Message)})

    m = Message(content="a", send_to=("a", MockRole, Message))
    assert m.send_to == set({"a", get_class_name(MockRole), get_class_name(Message)})


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
