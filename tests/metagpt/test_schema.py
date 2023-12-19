#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/20 10:40
@Author  : alexanderwu
@File    : test_schema.py
@Modified By: mashenquan, 2023-11-1. In line with Chapter 2.2.1 and 2.2.2 of RFC 116, introduce unit tests for
            the utilization of the new feature of `Message` class.
"""
import json

import pytest

from metagpt.actions import Action
from metagpt.schema import AIMessage, Message, SystemMessage, UserMessage
from metagpt.utils.common import any_to_str


def test_messages():
    test_content = "test_message"
    msgs = [
        UserMessage(test_content),
        SystemMessage(test_content),
        AIMessage(test_content),
        Message(test_content, role="QA"),
    ]
    text = str(msgs)
    roles = ["user", "system", "assistant", "QA"]
    assert all([i in text for i in roles])


def test_message():
    m = Message("a", role="v1")
    v = m.dump()
    d = json.loads(v)
    assert d
    assert d.get("content") == "a"
    assert d.get("role") == "v1"
    m.role = "v2"
    v = m.dump()
    assert v
    m = Message.load(v)
    assert m.content == "a"
    assert m.role == "v2"

    m = Message("a", role="b", cause_by="c", x="d", send_to="c")
    assert m.content == "a"
    assert m.role == "b"
    assert m.send_to == {"c"}
    assert m.cause_by == "c"

    m.cause_by = "Message"
    assert m.cause_by == "Message"
    m.cause_by = Action
    assert m.cause_by == any_to_str(Action)
    m.cause_by = Action()
    assert m.cause_by == any_to_str(Action)
    m.content = "b"
    assert m.content == "b"


def test_routes():
    m = Message("a", role="b", cause_by="c", x="d", send_to="c")
    m.send_to = "b"
    assert m.send_to == {"b"}
    m.send_to = {"e", Action}
    assert m.send_to == {"e", any_to_str(Action)}


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
