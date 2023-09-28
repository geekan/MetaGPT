#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : maze environment

from metagpt.environment import Environment
from .maze import Maze


class MazeEnvironment(Environment):
    def __init__(self, name: str, maze: Maze) -> None:
        self.name = name
        self.maze = maze
