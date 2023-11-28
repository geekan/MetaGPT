#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : product_manager.py
"""
from pydantic import Field

from metagpt.actions import BossRequirement, WritePRD
from metagpt.roles.role import Role


class ProductManager(Role):
    """
    Initializes the ProductManager role with given attributes.

    Args:
        name (str): Name of the product manager.
        profile (str): Role profile.
        goal (str): Goal of the product manager.
        constraints (str): Constraints or limitations for the product manager.
    """
    name: str = "Alice"
    role_profile: str = Field(default="Product Manager", alias='profile')
    goal: str = "Efficiently create a successful product"
    constraints: str = ""
    """
    Represents a Product Manager role responsible for product development and management.
    """
    def __init__(
            self,
            **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self._init_actions([WritePRD])
        self._watch([BossRequirement])
