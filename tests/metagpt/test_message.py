#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/16 10:57
@Author  : alexanderwu
@File    : test_message.py
"""
import pytest

from metagpt.schema import AIMessage, Message, RawMessage, SystemMessage, UserMessage


def test_message():
    msg = Message(role='User', content='WTF')
    assert msg.to_dict()['role'] == 'User'
    assert 'User' in str(msg)


def test_all_messages():
    test_content = 'test_message'
    msgs = [
        UserMessage(test_content),
        SystemMessage(test_content),
        AIMessage(test_content),
        Message(test_content, role='QA')
    ]
    for msg in msgs:
        assert msg.content == test_content


def test_raw_message():
    msg = RawMessage(role='user', content='raw')
    assert msg['role'] == 'user'
    assert msg['content'] == 'raw'
    with pytest.raises(KeyError):
        assert msg['1'] == 1, "KeyError: '1'"
