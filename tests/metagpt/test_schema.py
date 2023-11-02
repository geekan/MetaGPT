#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/20 10:40
@Author  : alexanderwu
@File    : test_schema.py
@Modified By: mashenquan, 2023-11-1. Add `test_message`.
"""
import json

import pytest

from metagpt.schema import AIMessage, Message, SystemMessage, UserMessage


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
    v = m.save()
    d = json.loads(v)
    assert d
    assert d.get("content") == "a"
    assert d.get("meta_info") == {"role": "v1"}
    m.set_role("v2")
    v = m.save()
    assert v
    m = Message.load(v)
    assert m.content == "a"
    assert m.role == "v2"


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
