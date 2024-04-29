#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 15:04
@Author  : alexanderwu
@File    : project_manager.py
"""

from metagpt.actions import UserRequirement, WriteTasks
from metagpt.actions.design_api import WriteDesign
from metagpt.actions.prepare_documents import PrepareDocuments
from metagpt.roles.role import Role
from metagpt.utils.common import any_to_str


class ProjectManager(Role):
    """
    Represents a Project Manager role responsible for overseeing project execution and team efficiency.

    Attributes:
        name (str): Name of the project manager.
        profile (str): Role profile, default is 'Project Manager'.
        goal (str): Goal of the project manager.
        constraints (str): Constraints or limitations for the project manager.
    """

    name: str = "Eve"
    profile: str = "Project Manager"
    goal: str = (
        "break down tasks according to PRD/technical design, generate a task list, and analyze task "
        "dependencies to start with the prerequisite modules"
    )
    constraints: str = "use same language as user requirement"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.set_actions([PrepareDocuments(send_to=any_to_str(self), context=self.context), WriteTasks])
        self._watch([UserRequirement, PrepareDocuments, WriteDesign])

    async def _think(self) -> bool:
        """Decide what to do"""
        mappings = {
            any_to_str(UserRequirement): 0,
            any_to_str(PrepareDocuments): 1,
            any_to_str(WriteDesign): 1,
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
