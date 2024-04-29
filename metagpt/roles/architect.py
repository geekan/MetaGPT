#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : architect.py
"""

from metagpt.actions import UserRequirement, WritePRD
from metagpt.actions.design_api import WriteDesign
from metagpt.actions.prepare_documents import PrepareDocuments
from metagpt.roles.role import Role
from metagpt.utils.common import any_to_str


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
    profile: str = "Architect"
    goal: str = "design a concise, usable, complete software system"
    constraints: str = (
        "make sure the architecture is simple enough and use  appropriate open source "
        "libraries. Use same language as user requirement"
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Initialize actions specific to the Architect role
        self.set_actions([PrepareDocuments(send_to=any_to_str(self), context=self.context), WriteDesign])

        # Set events or actions the Architect should watch or be aware of
        self._watch({UserRequirement, PrepareDocuments, WritePRD})

    async def _think(self) -> bool:
        """Decide what to do"""
        mappings = {
            any_to_str(UserRequirement): 0,
            any_to_str(PrepareDocuments): 1,
            any_to_str(WritePRD): 1,
        }
        for i in self.rc.news:
            idx = mappings.get(i.cause_by, -1)
            if idx < 0:
                continue
            self.rc.todo = self.actions[idx]
            return bool(self.rc.todo)
        return False

    async def _observe(self, ignore_memory=False) -> int:
        return await super()._observe(ignore_memory=True)
