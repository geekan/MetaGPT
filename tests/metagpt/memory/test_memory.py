#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of Memory

from metagpt.actions import UserRequirement
from metagpt.memory.memory import Memory
from metagpt.schema import Message


def test_memory():
    memory = Memory()

    message1 = Message(content="test message1", role="user1")
    message2 = Message(content="test message2", role="user2")
    message3 = Message(content="test message3", role="user1")
    memory.add(message1)
    assert memory.count() == 1

    memory.delete_newest()
    assert memory.count() == 0

    memory.add_batch([message1, message2])
    assert memory.count() == 2
    assert len(memory.index.get(message1.cause_by)) == 2

    messages = memory.get_by_role("user1")
    assert messages[0].content == message1.content

    messages = memory.get_by_content("test message")
    assert len(messages) == 2

    messages = memory.get_by_action(UserRequirement)
    assert len(messages) == 2

    messages = memory.get_by_actions({UserRequirement})
    assert len(messages) == 2

    messages = memory.try_remember("test message")
    assert len(messages) == 2

    messages = memory.get(k=1)
    assert len(messages) == 1

    messages = memory.get(k=5)
    assert len(messages) == 2

    messages = memory.find_news([message3])
    assert len(messages) == 1

    memory.delete(message1)
    assert memory.count() == 1
    messages = memory.get_by_role("user2")
    assert messages[0].content == message2.content

    memory.clear()
    assert memory.count() == 0
    assert len(memory.index) == 0
