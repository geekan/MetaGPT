"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: spatial_memory.py
Description: Defines the MemoryTree class that serves as the agents' spatial
memory that aids in grounding their behavior in the game world.
"""
from pathlib import Path

from pydantic import BaseModel, Field

from metagpt.logs import logger
from metagpt.utils.common import read_json_file, write_json_file


class MemoryTree(BaseModel):
    tree: dict = Field(default=dict)

    def set_mem_path(self, f_saved: Path):
        self.tree = read_json_file(f_saved)

    def print_tree(self) -> None:
        def _print_tree(tree, depth):
            dash = " >" * depth
            if isinstance(tree, list):
                if tree:
                    logger.info(f"{dash} {tree}")
                return

            for key, val in tree.items():
                if key:
                    logger.info(f"{dash} {tree}")
                _print_tree(val, depth + 1)

        _print_tree(self.tree, 0)

    def save(self, out_json: Path) -> None:
        write_json_file(out_json, self.tree)

    def get_str_accessible_sectors(self, curr_world: str) -> str:
        """
        Returns a summary string of all the arenas that the persona can access
        within the current sector.

        Note that there are places a given persona cannot enter. This information
        is provided in the persona sheet. We account for this in this function.

        INPUT
          None
        OUTPUT
          A summary string of all the arenas that the persona can access.
        EXAMPLE STR OUTPUT
          "bedroom, kitchen, dining room, office, bathroom"
        """
        x = ", ".join(list(self.tree[curr_world].keys()))
        return x

    def get_str_accessible_sector_arenas(self, sector: str) -> str:
        """
        Returns a summary string of all the arenas that the persona can access
        within the current sector.

        Note that there are places a given persona cannot enter. This information
        is provided in the persona sheet. We account for this in this function.

        INPUT
          None
        OUTPUT
          A summary string of all the arenas that the persona can access.
        EXAMPLE STR OUTPUT
          "bedroom, kitchen, dining room, office, bathroom"
        """
        curr_world, curr_sector = sector.split(":")
        if not curr_sector:
            return ""
        x = ", ".join(list(self.tree[curr_world][curr_sector].keys()))
        return x

    def get_str_accessible_arena_game_objects(self, arena: str) -> str:
        """
        Get a str list of all accessible game objects that are in the arena. If
        temp_address is specified, we return the objects that are available in
        that arena, and if not, we return the objects that are in the arena our
        persona is currently in.

        INPUT
          temp_address: optional arena address
        OUTPUT
          str list of all accessible game objects in the gmae arena.
        EXAMPLE STR OUTPUT
          "phone, charger, bed, nightstand"
        """
        curr_world, curr_sector, curr_arena = arena.split(":")

        if not curr_arena:
            return ""

        try:
            x = ", ".join(list(self.tree[curr_world][curr_sector][curr_arena]))
        except Exception:
            x = ", ".join(list(self.tree[curr_world][curr_sector][curr_arena.lower()]))
        return x

    def add_tile_info(self, tile_info: dict) -> None:
        if tile_info["world"]:
            if tile_info["world"] not in self.tree:
                self.tree[tile_info["world"]] = {}
        if tile_info["sector"]:
            if tile_info["sector"] not in self.tree[tile_info["world"]]:
                self.tree[tile_info["world"]][tile_info["sector"]] = {}
        if tile_info["arena"]:
            if tile_info["arena"] not in self.tree[tile_info["world"]][tile_info["sector"]]:
                self.tree[tile_info["world"]][tile_info["sector"]][tile_info["arena"]] = []
        if tile_info["game_object"]:
            if tile_info["game_object"] not in self.tree[tile_info["world"]][tile_info["sector"]][tile_info["arena"]]:
                self.tree[tile_info["world"]][tile_info["sector"]][tile_info["arena"]] += [tile_info["game_object"]]
