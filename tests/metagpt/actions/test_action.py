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


def test_action_serdes():
    action_info = WriteTest.ser_class()
    assert action_info["action_class"] == "WriteTest"

    action_class = Action.deser_class(action_info)
    assert action_class == WriteTest


def test_action_class_serdes():
    name = "write test"
    action_info = WriteTest(name=name).serialize()
    assert action_info["name"] == name

    action = Action.deserialize(action_info)
    assert action.name == name
