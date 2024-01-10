#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/16 10:57
@Author  : alexanderwu
@File    : test_message.py
@Modified By: mashenquan, 2023-11-1. Modify coding style.
"""
import pytest

from metagpt.schema import AIMessage, Message, SystemMessage, UserMessage


def test_message():
    msg = Message(role="User", content="WTF")
    assert msg.to_dict()["role"] == "User"
    assert "User" in str(msg)


def test_all_messages():
    test_content = "test_message"
    msgs = [
        UserMessage(test_content),
        SystemMessage(test_content),
        AIMessage(test_content),
        Message(content=test_content, role="QA"),
    ]
    for msg in msgs:
        assert msg.content == test_content


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
