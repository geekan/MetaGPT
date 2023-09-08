#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : architect.py
"""

from metagpt.actions import WritePRD
from metagpt.actions.design_api import WriteDesign
from metagpt.roles import Role


class Architect(Role):
    """
    Represents an Architect role in a software development process.

    Attributes:
        name (str): Name of the architect.
        profile (str): Role profile, default is 'Architect'.
        goal (str): Primary goal or responsibility of the architect.
        constraints (str): Constraints or guidelines for the architect.
    """

    def __init__(
        self,
        name: str = "Bob",
        profile: str = "Architect",
        goal: str = "Design a concise, usable, complete python system",
        constraints: str = "Try to specify good open source tools as much as possible",
    ) -> None:
        """Initializes the Architect with given attributes."""
        super().__init__(name, profile, goal, constraints)

        # Initialize actions specific to the Architect role
        self._init_actions([WriteDesign])

        # Set events or actions the Architect should watch or be aware of
        self._watch({WritePRD})
