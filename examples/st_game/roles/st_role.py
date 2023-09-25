#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : Stanford Town role

"""
Do the steps following:
- perceive, receive environment(Maze) info
- retrieve, retrieve memories
- plan, do plan like long-term plan and interact with Maze
- reflect, do the High-level thinking based on memories and re-add into the memory
- execute, move or else in the Maze
"""

from pydantic import Field
from pathlib import Path

from metagpt.roles.role import Role, RoleContext

from ..memory.associative_memory import AssociativeMemory


class STRoleContext(RoleContext):

    memory: AssociativeMemory = Field(default=AssociativeMemory)


class STRole(Role):

    # add a role's property structure to store role's age and so on like GA's Scratch.

    def __init__(self, name="", profile=""):
        self._rc = STRoleContext()

    def load_from(self, folder: Path):
        """
        load role data from `storage/{simulation_name}/personas/{role_name}
        """
        pass

    def save_into(self, folder: Path):
        """
        save role data from `storage/{simulation_name}/personas/{role_name}
        """
        pass
