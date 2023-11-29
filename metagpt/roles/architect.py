#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : architect.py
"""

from metagpt.actions import WritePRD, ActionOutput
from metagpt.actions.design_api import WriteDesign
from metagpt.actions.refine_design_api import RefineDesign
from metagpt.actions.refine_prd import RefinePRD
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message


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
            increment: bool = False,
    ) -> None:
        """Initializes the Architect with given attributes."""
        super().__init__(name, profile, goal, constraints)
        self.increment = increment

        # Initialize actions specific to the Architect role
        # Set events or actions the Architect should watch or be aware of
        if self.increment:
            self._init_actions([RefineDesign])
            self._watch({RefinePRD})
        else:
            self._init_actions([WriteDesign])
            self._watch({WritePRD})

    async def _act(self) -> Message:
        if self.increment:
            logger.info(f"{self._setting}: ready to RefineDesign")
            legacy = self._rc.env.get_legacy()["legacy_design"]
            response = await self._rc.todo.run(self._rc.history, legacy)

        else:
            logger.info(f"{self._setting}: ready to WriteDesign")
            response = await self._rc.todo.run(self._rc.history)

        if isinstance(response, ActionOutput):
            msg = Message(content=response.content, instruct_content=response.instruct_content,
                          role=self.profile, cause_by=type(self._rc.todo))
        else:
            msg = Message(content=response, role=self.profile, cause_by=type(self._rc.todo))
        self._rc.memory.add(msg)
        logger.debug(f"{response}")

        return msg
