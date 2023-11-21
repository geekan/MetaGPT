#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 15:04
@Author  : alexanderwu
@File    : project_manager.py
"""
from metagpt.actions import WriteTasks, ActionOutput
from metagpt.actions.design_api import WriteDesign
from metagpt.actions.refine_design_api import RefineDesign
from metagpt.actions.refine_project_management import RefineTasks
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message


class ProjectManager(Role):
    """
    Represents a Project Manager role responsible for overseeing project execution and team efficiency.

    Attributes:
        name (str): Name of the project manager.
        profile (str): Role profile, default is 'Project Manager'.
        goal (str): Goal of the project manager.
        constraints (str): Constraints or limitations for the project manager.
    """

    def __init__(
        self,
        name: str = "Eve",
        profile: str = "Project Manager",
        goal: str = "Improve team efficiency and deliver with quality and quantity",
        constraints: str = "",
        increment: bool = False,
        legacy: str = "",
    ) -> None:
        """
        Initializes the ProjectManager role with given attributes.

        Args:
            name (str): Name of the project manager.
            profile (str): Role profile.
            goal (str): Goal of the project manager.
            constraints (str): Constraints or limitations for the project manager.
        """
        super().__init__(name, profile, goal, constraints)
        self.increment = increment
        self.legacy = legacy

        if self.increment:
            self._init_actions([RefineTasks])
            self._watch([RefineDesign])
        else:
            self._init_actions([WriteTasks])
            self._watch([WriteDesign])

    async def _act(self) -> Message:
        if self.increment:
            logger.info(f"{self._setting}: ready to RefineTasks")
            response = await self._rc.todo.run(self._rc.history, self.legacy)

        else:
            logger.info(f"{self._setting}: ready to WriteTasks")
            response = await self._rc.todo.run(self._rc.history)

        if isinstance(response, ActionOutput):
            msg = Message(content=response.content, instruct_content=response.instruct_content,
                          role=self.profile, cause_by=type(self._rc.todo))
        else:
            msg = Message(content=response, role=self.profile, cause_by=type(self._rc.todo))
        self._rc.memory.add(msg)
        logger.debug(f"{response}")

        return msg
