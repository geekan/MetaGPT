#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : product_manager.py
@Modified By: mashenquan, 2023/8/20. Remove global configuration `CONFIG`, enable configuration support for business isolation;
            Change cost control from global to company level.
"""
from metagpt.actions import BossRequirement, WritePRD
from metagpt.roles import Role


class ProductManager(Role):
    def __init__(self, options, cost_manager, name="Alice", profile="Product Manager", goal="Efficiently create a successful product",
                 constraints=""):
        super().__init__(name=name, profile=profile, goal=goal, constraints=constraints, options=options, cost_manager=cost_manager)
        self._init_actions([WritePRD])
        self._watch([BossRequirement])
