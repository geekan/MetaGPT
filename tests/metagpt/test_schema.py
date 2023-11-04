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
from metagpt.schema import AIMessage, Message, Routes, SystemMessage, UserMessage


@pytest.mark.asyncio
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


@pytest.mark.asyncio
def test_message():
    m = Message("a", role="v1")
    v = m.dump()
    d = json.loads(v)
    assert d
    assert d.get("content") == "a"
    assert d.get("meta_info") == {"role": "v1"}
    m.set_role("v2")
    v = m.dump()
    assert v
    m = Message.load(v)
    assert m.content == "a"
    assert m.role == "v2"

    m = Message("a", role="b", cause_by="c", x="d")
    assert m.content == "a"
    assert m.role == "b"
    assert m.is_recipient({"c"})
    assert m.cause_by == "c"
    assert m.get_meta("x") == "d"

    m.cause_by = "Message"
    assert m.cause_by == "Message"
    m.cause_by = Action
    assert m.cause_by == Action.get_class_name()
    m.cause_by = Action()
    assert m.cause_by == Action.get_class_name()
    m.content = "b"
    assert m.content == "b"


@pytest.mark.asyncio
def test_routes():
    route = Routes()
    route.set_from("a")
    assert route.tx_from == "a"
    route.add_to("b")
    assert route.tx_to == {"b"}
    route.add_to("c")
    assert route.tx_to == {"b", "c"}
    route.set_to({"e", "f"})
    assert route.tx_to == {"e", "f"}
    assert route.is_recipient({"e"})
    assert route.is_recipient({"f"})
    assert not route.is_recipient({"a"})


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
