#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : maze environment

from pydantic import Field

from metagpt.environment import Environment
from metagpt.roles.role import Role

from .maze import Maze


class MazeEnvironment(Environment):

    maze: Maze = Field(default=Maze)

    def add_role(self, role: Role):
        role.set_env(self)
        self.roles[role.name] = role  # use role.name as key not role.profile
