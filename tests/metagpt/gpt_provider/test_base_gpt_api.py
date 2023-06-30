#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/7 17:40
@Author  : alexanderwu
@File    : test_base_gpt_api.py
"""

from metagpt.schema import Message


def test_message():
    message = Message(role='user', content='wtf')
    assert 'role' in message.to_dict()
    assert 'user' in str(message)
