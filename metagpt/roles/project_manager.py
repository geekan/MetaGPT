#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 15:04
@Author  : alexanderwu
@File    : project_manager.py
"""
from metagpt.roles import Role
from metagpt.actions import WriteTasks, AssignTasks, WriteDesign


class ProjectManager(Role):
    def __init__(self, name="Eve", profile="Project Manager",
                 goal="Improve team efficiency and deliver with quality and quantity", constraints=""):
        super().__init__(name, profile, goal, constraints)
        self._init_actions([WriteTasks])
        self._watch([WriteDesign])
