#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : test_action.py
"""
from metagpt.actions import Action, WritePRD, WriteTest


def test_action_repr():
    actions = [Action(), WriteTest(), WritePRD()]
    assert "WriteTest" in str(actions)
