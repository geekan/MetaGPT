#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : test_action.py
"""

import pytest

from metagpt.actions import Action, WritePRD, WriteTest
from metagpt.logs import logger


def test_action_repr():
    actions = [Action(), WriteTest(), WritePRD()]
    assert "WriteTest" in str(actions)
