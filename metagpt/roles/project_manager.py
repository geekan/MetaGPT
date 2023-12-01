#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 15:04
@Author  : alexanderwu
@File    : project_manager.py
"""
from pydantic import Field

from metagpt.actions import WriteTasks
from metagpt.actions.design_api import WriteDesign
from metagpt.roles.role import Role


class ProjectManager(Role):
    """
    Represents a Project Manager role responsible for overseeing project execution and team efficiency.

    Attributes:
        name (str): Name of the project manager.
        profile (str): Role profile, default is 'Project Manager'.
        goal (str): Goal of the project manager.
        constraints (str): Constraints or limitations for the project manager.
    """
    name: str = Field(default="Eve")
    profile: str = Field(default="Project Manager")
    
    goal: str = "Improve team efficiency and deliver with quality and quantity"
    constraints: str = ""

    def __init__(
            self,
            **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self._init_actions([WriteTasks])
        self._watch([WriteDesign])
