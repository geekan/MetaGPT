#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of Role
import pytest

from metagpt.provider.human_provider import HumanProvider
from metagpt.roles.role import Role
from metagpt.schema import Message, UserMessage


def test_role_desc():
    role = Role(profile="Sales", desc="Best Seller")
    assert role.profile == "Sales"
    assert role.desc == "Best Seller"


def test_role_human(context):
    role = Role(is_human=True, context=context)
    assert isinstance(role.llm, HumanProvider)


@pytest.mark.asyncio
async def test_recovered():
    role = Role(profile="Tester", desc="Tester", recovered=True)
    role.put_message(UserMessage(content="2"))
    role.latest_observed_msg = Message(content="1")
    await role._observe()
    await role._observe()
    assert role.rc.msg_buffer.empty()


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
