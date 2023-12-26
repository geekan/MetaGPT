#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : test_action.py
"""
from metagpt.actions import Action, ActionType, WritePRD, WriteTest


def test_action_repr():
    actions = [Action(), WriteTest(), WritePRD()]
    assert "WriteTest" in str(actions)


def test_action_type():
    assert ActionType.WRITE_PRD.value == WritePRD
    assert ActionType.WRITE_TEST.value == WriteTest
    assert ActionType.WRITE_PRD.name == "WRITE_PRD"
    assert ActionType.WRITE_TEST.name == "WRITE_TEST"
