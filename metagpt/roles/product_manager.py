#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : product_manager.py
"""
from metagpt.actions import BossRequirement, WritePRD, ActionOutput
from metagpt.actions.refine_prd import RefinePRD
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message


class ProductManager(Role):
    """
    Represents a Product Manager role responsible for product development and management.

    Attributes:
        name (str): Name of the product manager.
        profile (str): Role profile, default is 'Product Manager'.
        goal (str): Goal of the product manager.
        constraints (str): Constraints or limitations for the product manager.
    """

    def __init__(
        self,
        name: str = "Alice",
        profile: str = "Product Manager",
        goal: str = "Efficiently create a successful product",
        constraints: str = "",
        increment: bool = False,
    ) -> None:
        """
        Initializes the ProductManager role with given attributes.

        Args:
            name (str): Name of the product manager.
            profile (str): Role profile.
            goal (str): Goal of the product manager.
            constraints (str): Constraints or limitations for the product manager.
        """
        super().__init__(name, profile, goal, constraints)
        self.increment = increment

        if self.increment:
            self._init_actions([RefinePRD])
        else:
            self._init_actions([WritePRD])
        self._watch([BossRequirement])

    async def _act(self) -> Message:
        if self.increment:
            logger.info(f"{self._setting}: ready to RefinePRD")
            legacy_dict = self._rc.env.get_legacy()
            # legacy = "Legacy PRD:\n" + legacy_dict.get("legacy_prd") + "\nLegacy Code:\n" + legacy_dict.get("legacy_code")
            legacy = legacy_dict.get("legacy_prd")
            response = await self._rc.todo.run(self._rc.history, legacy)

        else:
            logger.info(f"{self._setting}: ready to WritePRD")
            response = await self._rc.todo.run(self._rc.history)

        if isinstance(response, ActionOutput):
            msg = Message(content=response.content, instruct_content=response.instruct_content,
                        role=self.profile, cause_by=type(self._rc.todo))
        else:
            msg = Message(content=response, role=self.profile, cause_by=type(self._rc.todo))
        self._rc.memory.add(msg)
        logger.debug(f"{response}")

        return msg
