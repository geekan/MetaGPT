#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : product_manager.py
@Modified By: mashenquan, 2023/11/27. Add `PrepareDocuments` action according to Section 2.2.3.5.1 of RFC 135.
"""

from pydantic import Field

from metagpt.actions import UserRequirement, WritePRD
from metagpt.actions.prepare_documents import PrepareDocuments
from metagpt.config import CONFIG
from metagpt.roles.role import Role


class ProductManager(Role):
    """
    Represents a Project Manager role responsible for overseeing project execution and team efficiency.

    Attributes:
        name (str): Name of the project manager.
        profile (str): Role profile, default is 'Project Manager'.
        goal (str): Goal of the project manager.
        constraints (str): Constraints or limitations for the project manager.
    """
    name: str = "Alice"
    role_profile: str = Field(default="Product Manager", alias='profile')
    goal: str = "efficiently create a successful product"
    constraints: str = "use same language as user requiremen"
    """
    Represents a Product Manager role responsible for product development and management.
    """
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self._init_actions([PrepareDocuments, WritePRD])
        self._watch([UserRequirement, PrepareDocuments])

    async def _think(self) -> None:
        """Decide what to do"""
        if CONFIG.git_repo:
            self._set_state(1)
        else:
            self._set_state(0)
        return self._rc.todo

    async def _observe(self, ignore_memory=False) -> int:
        return await super(ProductManager, self)._observe(ignore_memory=True)
