#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 15:04
@Author  : alexanderwu
@File    : project_manager.py
@Modified By: mashenquan, 2023/8/20. Remove global configuration `CONFIG`, enable configuration support for business isolation;
            Change cost control from global to company level.
"""
from metagpt.actions import WriteDesign, WriteTasks
from metagpt.roles import Role


class ProjectManager(Role):
    def __init__(self, options, cost_manager, name="Eve", profile="Project Manager",
                 goal="Improve team efficiency and deliver with quality and quantity", constraints=""):
        super().__init__(name=name, profile=profile, goal=goal, constraints=constraints, options=options, cost_manager=cost_manager)
        self._init_actions([WriteTasks])
        self._watch([WriteDesign])
