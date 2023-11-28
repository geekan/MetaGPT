#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : architect.py
"""
from pydantic import Field

from metagpt.actions import WritePRD
from metagpt.actions.design_api import WriteDesign
from metagpt.roles.role import Role


class Architect(Role):
    """
    Represents an Architect role in a software development process.

    Attributes:
        name (str): Name of the architect.
        profile (str): Role profile, default is 'Architect'.
        goal (str): Primary goal or responsibility of the architect.
        constraints (str): Constraints or guidelines for the architect.
    """
    name: str = "Bob"
    role_profile: str = Field(default="Architect" , alias='profile')
    goal: str = "Design a concise, usable, complete python system"
    constraints: str = "Try to specify good open source tools as much as possible"

    def __init__(
            self,
            **kwargs
    ) -> None:
        super().__init__(**kwargs)
        # Initialize actions specific to the Architect role
        self._init_actions([WriteDesign])

        # Set events or actions the Architect should watch or be aware of
        self._watch({WritePRD})
