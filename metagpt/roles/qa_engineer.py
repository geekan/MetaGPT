#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : qa_engineer.py
"""
from metagpt.actions.run_code import RunCode
from metagpt.actions import WriteTest
from metagpt.roles import Role


class QaEngineer(Role):
    def __init__(self, name, profile, goal, constraints):
        super().__init__(name, profile, goal, constraints)
        self._init_actions([WriteTest])
