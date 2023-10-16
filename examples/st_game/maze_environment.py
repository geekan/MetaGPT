#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : maze environment

from typing import Tuple
from pydantic import Field

from metagpt.environment.environment import Environment
from metagpt.environment.general_environment import GeneralEnvironment
from metagpt.roles.role import Role

from examples.st_game.maze import Maze


class MazeEnvironment(GeneralEnvironment):

    maze: Maze = Field(default_factory=Maze)

    def add_role(self, role: Role):
        self.roles[role.name] = role

    def init_register_funcs(self):
        self.register_func("access_tile", self.maze.access_tile)
        self.register_func("add_tiles_event", self.add_tiles_event)
        self.register_func("get_nearby_tiles", self.maze.get_nearby_tiles)
        self.register_func("get_tile_path", self.maze.get_tile_path)
        self.register_func("get_collision_maze", self.get_collision_maze)
        self.register_func("get_address_tiles", self.get_address_tiles)
        self.register_func("turn_event_from_tile_idle", self.maze.turn_event_from_tile_idle)
        self.register_func("remove_subject_events_from_tile", self.maze.remove_subject_events_from_tile)
        self.register_func("add_event_from_tile", self.maze.add_event_from_tile)
        self.register_func("remove_event_from_tile", self.maze.remove_event_from_tile)

    def add_tiles_event(self, pt_y: int, pt_x: int, event: Tuple[str, str, str, str]):
        self.maze.tiles[pt_y][pt_x]["events"].add(event)

    def get_collision_maze(self) -> list:
        return self.maze.collision_maze

    def get_address_tiles(self) -> dict:
        return self.maze.address_tiles
