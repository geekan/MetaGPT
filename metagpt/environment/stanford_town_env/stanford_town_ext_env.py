#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : The StanfordTown external environment to interate with the web interface
#           refs to `generative_agents maze.py`

import math
from pathlib import Path
from typing import Optional, Tuple

from pydantic import ConfigDict, Field, model_validator

from metagpt.environment.base_env import ExtEnv, mark_as_readable, mark_as_writeable
from metagpt.utils.common import read_csv_to_list, read_json_file


class StanfordTownExtEnv(ExtEnv):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    maze_asset_path: Optional[Path] = Field(default=None, description="the path to store maze assets")
    maze_width: int = Field(default=140, description="maze map width")
    maze_height: int = Field(default=100, description="maze map height")
    sq_tile_size: int = Field(default=32, description="the pixel height/width of a tile")
    special_constraint: str = Field(
        default="", description="a string description of any relevant special constraints " "the world might have"
    )
    tiles: list[list[dict]] = Field(default=[])
    address_tiles: dict[str, set] = Field(default=dict())
    collision_maze: list[list] = Field(default=[])

    @model_validator(mode="before")
    @classmethod
    def _init_maze(cls, values):
        maze_asset_path = values["maze_asset_path"]
        assert maze_asset_path
        maze_asset_path = Path(maze_asset_path)

        maze_matrix_path = maze_asset_path.joinpath("matrix")
        meta_info = read_json_file(maze_matrix_path.joinpath("maze_meta_info.json"))

        maze_width = int(meta_info["maze_width"])
        maze_height = int(meta_info["maze_height"])
        values["maze_width"] = maze_width
        values["maze_height"] = maze_height
        values["sq_tile_size"] = int(meta_info["sq_tile_size"])
        values["special_constraint"] = meta_info["special_constraint"]

        # READING IN SPECIAL BLOCKS
        # Special blocks are those that are colored in the Tiled map.
        # Here is an example row for the arena block file:
        # e.g, "25331, Double Studio, Studio, Bedroom 2, Painting"

        blocks_folder = maze_matrix_path.joinpath("special_blocks")

        _wb = blocks_folder.joinpath("world_blocks.csv")
        wb_rows = read_csv_to_list(_wb, header=False)
        wb = wb_rows[0][-1]

        _sb = blocks_folder.joinpath("sector_blocks.csv")
        sb_rows = read_csv_to_list(_sb, header=False)
        sb_dict = dict()
        for i in sb_rows:
            sb_dict[i[0]] = i[-1]

        _ab = blocks_folder.joinpath("arena_blocks.csv")
        ab_rows = read_csv_to_list(_ab, header=False)
        ab_dict = dict()
        for i in ab_rows:
            ab_dict[i[0]] = i[-1]

        _gob = blocks_folder.joinpath("game_object_blocks.csv")
        gob_rows = read_csv_to_list(_gob, header=False)
        gob_dict = dict()
        for i in gob_rows:
            gob_dict[i[0]] = i[-1]

        _slb = blocks_folder.joinpath("spawning_location_blocks.csv")
        slb_rows = read_csv_to_list(_slb, header=False)
        slb_dict = dict()
        for i in slb_rows:
            slb_dict[i[0]] = i[-1]

        # [SECTION 3] Reading in the matrices
        # This is your typical two dimensional matrices. It's made up of 0s and
        # the number that represents the color block from the blocks folder.
        maze_folder = maze_matrix_path.joinpath("maze")

        _cm = maze_folder.joinpath("collision_maze.csv")
        collision_maze_raw = read_csv_to_list(_cm, header=False)[0]
        _sm = maze_folder.joinpath("sector_maze.csv")
        sector_maze_raw = read_csv_to_list(_sm, header=False)[0]
        _am = maze_folder.joinpath("arena_maze.csv")
        arena_maze_raw = read_csv_to_list(_am, header=False)[0]
        _gom = maze_folder.joinpath("game_object_maze.csv")
        game_object_maze_raw = read_csv_to_list(_gom, header=False)[0]
        _slm = maze_folder.joinpath("spawning_location_maze.csv")
        spawning_location_maze_raw = read_csv_to_list(_slm, header=False)[0]

        # Loading the maze. The mazes are taken directly from the json exports of
        # Tiled maps. They should be in csv format.
        # Importantly, they are "not" in a 2-d matrix format -- they are single
        # row matrices with the length of width x height of the maze. So we need
        # to convert here.
        # example format: [['0', '0', ... '25309', '0',...], ['0',...]...]
        # 25309 is the collision bar number right now.
        collision_maze = []
        sector_maze = []
        arena_maze = []
        game_object_maze = []
        spawning_location_maze = []
        for i in range(0, len(collision_maze_raw), maze_width):
            tw = maze_width
            collision_maze += [collision_maze_raw[i : i + tw]]
            sector_maze += [sector_maze_raw[i : i + tw]]
            arena_maze += [arena_maze_raw[i : i + tw]]
            game_object_maze += [game_object_maze_raw[i : i + tw]]
            spawning_location_maze += [spawning_location_maze_raw[i : i + tw]]
        values["collision_maze"] = collision_maze

        tiles = []
        for i in range(maze_height):
            row = []
            for j in range(maze_width):
                tile_details = dict()
                tile_details["world"] = wb

                tile_details["sector"] = ""
                if sector_maze[i][j] in sb_dict:
                    tile_details["sector"] = sb_dict[sector_maze[i][j]]

                tile_details["arena"] = ""
                if arena_maze[i][j] in ab_dict:
                    tile_details["arena"] = ab_dict[arena_maze[i][j]]

                tile_details["game_object"] = ""
                if game_object_maze[i][j] in gob_dict:
                    tile_details["game_object"] = gob_dict[game_object_maze[i][j]]

                tile_details["spawning_location"] = ""
                if spawning_location_maze[i][j] in slb_dict:
                    tile_details["spawning_location"] = slb_dict[spawning_location_maze[i][j]]

                tile_details["collision"] = False
                if collision_maze[i][j] != "0":
                    tile_details["collision"] = True

                tile_details["events"] = set()

                row += [tile_details]
            tiles += [row]
        values["tiles"] = tiles

        # Each game object occupies an event in the tile. We are setting up the
        # default event value here.
        for i in range(maze_height):
            for j in range(maze_width):
                if tiles[i][j]["game_object"]:
                    object_name = ":".join(
                        [tiles[i][j]["world"], tiles[i][j]["sector"], tiles[i][j]["arena"], tiles[i][j]["game_object"]]
                    )
                    go_event = (object_name, None, None, None)
                    tiles[i][j]["events"].add(go_event)

        # Reverse tile access.
        # <address_tiles> -- given a string address, we return a set of all
        # tile coordinates belonging to that address (this is opposite of
        # tiles that give you the string address given a coordinate). This is
        # an optimization component for finding paths for the personas' movement.
        # address_tiles['<spawn_loc>bedroom-2-a'] == {(58, 9)}
        # address_tiles['double studio:recreation:pool table']
        #   == {(29, 14), (31, 11), (30, 14), (32, 11), ...},
        address_tiles = dict()
        for i in range(maze_height):
            for j in range(maze_width):
                addresses = []
                if tiles[i][j]["sector"]:
                    add = f'{tiles[i][j]["world"]}:'
                    add += f'{tiles[i][j]["sector"]}'
                    addresses += [add]
                if tiles[i][j]["arena"]:
                    add = f'{tiles[i][j]["world"]}:'
                    add += f'{tiles[i][j]["sector"]}:'
                    add += f'{tiles[i][j]["arena"]}'
                    addresses += [add]
                if tiles[i][j]["game_object"]:
                    add = f'{tiles[i][j]["world"]}:'
                    add += f'{tiles[i][j]["sector"]}:'
                    add += f'{tiles[i][j]["arena"]}:'
                    add += f'{tiles[i][j]["game_object"]}'
                    addresses += [add]
                if tiles[i][j]["spawning_location"]:
                    add = f'<spawn_loc>{tiles[i][j]["spawning_location"]}'
                    addresses += [add]

                for add in addresses:
                    if add in address_tiles:
                        address_tiles[add].add((j, i))
                    else:
                        address_tiles[add] = set([(j, i)])
        values["address_tiles"] = address_tiles
        return values

    def turn_coordinate_to_tile(self, px_coordinate: tuple[int, int]) -> tuple[int, int]:
        """
        Turns a pixel coordinate to a tile coordinate.
        """
        x = math.ceil(px_coordinate[0] / self.sq_tile_size)
        y = math.ceil(px_coordinate[1] / self.sq_tile_size)
        return (x, y)

    @mark_as_readable
    def get_collision_maze(self) -> list:
        return self.collision_maze

    @mark_as_readable
    def get_address_tiles(self) -> dict:
        return self.address_tiles

    @mark_as_readable
    def access_tile(self, tile: tuple[int, int]) -> dict:
        """
        Returns the tiles details dictionary that is stored in self.tiles of the
        designated x, y location.

        INPUT
          tile: The tile coordinate of our interest in (x, y) form.
        OUTPUT
          The tile detail dictionary for the designated tile.
        EXAMPLE OUTPUT
          Given (58, 9),
          self.tiles[9][58] = {'world': 'double studio',
                'sector': 'double studio', 'arena': 'bedroom 2',
                'game_object': 'bed', 'spawning_location': 'bedroom-2-a',
                'collision': False,
                'events': {('double studio:double studio:bedroom 2:bed',
                           None, None)}}
        """
        x = tile[0]
        y = tile[1]
        return self.tiles[y][x]

    @mark_as_readable
    def get_tile_path(self, tile: tuple[int, int], level: str) -> str:
        """
        Get the tile string address given its coordinate. You designate the level
        by giving it a string level description.

        INPUT:
          tile: The tile coordinate of our interest in (x, y) form.
          level: world, sector, arena, or game object
        OUTPUT
          The string address for the tile.
        EXAMPLE OUTPUT
          Given tile=(58, 9), and level=arena,
          "double studio:double studio:bedroom 2"
        """
        x = tile[0]
        y = tile[1]
        tile = self.tiles[y][x]

        path = f"{tile['world']}"
        if level == "world":
            return path
        else:
            path += f":{tile['sector']}"

        if level == "sector":
            return path
        else:
            path += f":{tile['arena']}"

        if level == "arena":
            return path
        else:
            path += f":{tile['game_object']}"

        return path

    @mark_as_readable
    def get_nearby_tiles(self, tile: tuple[int, int], vision_r: int) -> list[tuple[int, int]]:
        """
        Given the current tile and vision_r, return a list of tiles that are
        within the radius. Note that this implementation looks at a square
        boundary when determining what is within the radius.
        i.e., for vision_r, returns x's.
        x x x x x
        x x x x x
        x x P x x
        x x x x x
        x x x x x

        INPUT:
          tile: The tile coordinate of our interest in (x, y) form.
          vision_r: The radius of the persona's vision.
        OUTPUT:
          nearby_tiles: a list of tiles that are within the radius.
        """
        left_end = 0
        if tile[0] - vision_r > left_end:
            left_end = tile[0] - vision_r

        right_end = self.maze_width - 1
        if tile[0] + vision_r + 1 < right_end:
            right_end = tile[0] + vision_r + 1

        bottom_end = self.maze_height - 1
        if tile[1] + vision_r + 1 < bottom_end:
            bottom_end = tile[1] + vision_r + 1

        top_end = 0
        if tile[1] - vision_r > top_end:
            top_end = tile[1] - vision_r

        nearby_tiles = []
        for i in range(left_end, right_end):
            for j in range(top_end, bottom_end):
                nearby_tiles += [(i, j)]
        return nearby_tiles

    @mark_as_writeable
    def add_tiles_event(self, pt_y: int, pt_x: int, event: Tuple[str, str, str, str]):
        self.tiles[pt_y][pt_x]["events"].add(event)

    @mark_as_writeable
    def add_event_from_tile(self, curr_event: tuple[str], tile: tuple[int, int]) -> None:
        """
        Add an event triple to a tile.

        INPUT:
          curr_event: Current event triple.
            e.g., ('double studio:double studio:bedroom 2:bed', None,
                    None)
          tile: The tile coordinate of our interest in (x, y) form.
        OUPUT:
          None
        """
        self.tiles[tile[1]][tile[0]]["events"].add(curr_event)

    @mark_as_writeable
    def remove_event_from_tile(self, curr_event: tuple[str], tile: tuple[int, int]) -> None:
        """dswaq
        Remove an event triple from a tile.

        INPUT:
          curr_event: Current event triple.
            e.g., ('double studio:double studio:bedroom 2:bed', None,
                    None)
          tile: The tile coordinate of our interest in (x, y) form.
        OUPUT:
          None
        """
        curr_tile_ev_cp = self.tiles[tile[1]][tile[0]]["events"].copy()
        for event in curr_tile_ev_cp:
            if event == curr_event:
                self.tiles[tile[1]][tile[0]]["events"].remove(event)

    @mark_as_writeable
    def turn_event_from_tile_idle(self, curr_event: tuple[str], tile: tuple[int, int]) -> None:
        curr_tile_ev_cp = self.tiles[tile[1]][tile[0]]["events"].copy()
        for event in curr_tile_ev_cp:
            if event == curr_event:
                self.tiles[tile[1]][tile[0]]["events"].remove(event)
                new_event = (event[0], None, None, None)
                self.tiles[tile[1]][tile[0]]["events"].add(new_event)

    @mark_as_writeable
    def remove_subject_events_from_tile(self, subject: str, tile: tuple[int, int]) -> None:
        """
        Remove an event triple that has the input subject from a tile.

        INPUT:
          subject: "Isabella Rodriguez"
          tile: The tile coordinate of our interest in (x, y) form.
        OUPUT:
          None
        """
        curr_tile_ev_cp = self.tiles[tile[1]][tile[0]]["events"].copy()
        for event in curr_tile_ev_cp:
            if event[0] == subject:
                self.tiles[tile[1]][tile[0]]["events"].remove(event)
