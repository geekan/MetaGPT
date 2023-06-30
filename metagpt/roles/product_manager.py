#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : product_manager.py
"""
from metagpt.roles import Role
from metagpt.actions import WritePRD, BossRequirement
from metagpt.schema import Message


class ProductManager(Role):
    def __init__(self, name="Alice", profile="Product Manager", goal="Efficiently create a successful product",
                 constraints=""):
        super().__init__(name, profile, goal, constraints)
        self._init_actions([WritePRD])
        self._watch([BossRequirement])
