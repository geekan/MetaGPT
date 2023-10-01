#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : maze environment

"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: maze.py
Description: Defines the Maze class, which represents the map of the simulated
world in a 2-dimensional matrix.
"""

import json
import math
from pathlib import Path
import networkx as nx
from .utils.const import MAZE_ASSET_PATH
from .utils.utils import read_csv_to_list


class Maze:
    def __init__(self, maze_asset_path: Path = MAZE_ASSET_PATH) -> None:
        # READING IN THE BASIC META INFORMATION ABOUT THE MAP
        self.maze_asset_path = maze_asset_path
        maze_matrix_path = maze_asset_path.joinpath("matrix")
        # Reading in the meta information about the world. If you want tp see the
        # example variables, check out the maze_meta_info.json file.
        meta_info = json.load(open(maze_matrix_path.joinpath("maze_meta_info.json")))
        # <maze_width> and <maze_height> denote the number of tiles make up the
        # height and width of the map.
        self.maze_width = int(meta_info["maze_width"])
        self.maze_height = int(meta_info["maze_height"])
        # <sq_tile_size> denotes the pixel height/width of a tile.
        self.sq_tile_size = int(meta_info["sq_tile_size"])
        # <special_constraint> is a string description of any relevant special
        # constraints the world might have.
        # e.g., "planning to stay at home all day and never go out of her home"
        self.special_constraint = meta_info["special_constraint"]

        # READING IN SPECIAL BLOCKS
        # Special blocks are those that are colored in the Tiled map.

        # Here is an example row for the arena block file:
        # e.g., "25335, Double Studio, Studio, Common Room"
        # And here is another example row for the game object block file:
        # e.g, "25331, Double Studio, Studio, Bedroom 2, Painting"

        # Notice that the first element here is the color marker digit from the
        # Tiled export. Then we basically have the block path:
        # World, Sector, Arena, Game Object -- again, these paths need to be
        # unique within an instance of Reverie.
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
        # We can do this all at once since the dimension of all these matrices are
        # identical (e.g., 70 x 40).
        # example format: [['0', '0', ... '25309', '0',...], ['0',...]...]
        # 25309 is the collision bar number right now.
        self.collision_maze = []
        sector_maze = []
        arena_maze = []
        game_object_maze = []
        spawning_location_maze = []
        for i in range(0, len(collision_maze_raw), meta_info["maze_width"]):
            tw = meta_info["maze_width"]
            self.collision_maze += [collision_maze_raw[i:i + tw]]
            sector_maze += [sector_maze_raw[i:i + tw]]
            arena_maze += [arena_maze_raw[i:i + tw]]
            game_object_maze += [game_object_maze_raw[i:i + tw]]
            spawning_location_maze += [spawning_location_maze_raw[i:i + tw]]

        # Once we are done loading in the maze, we now set up self.tiles. This is
        # a matrix accessed by row:col where each access point is a dictionary
        # that contains all the things that are taking place in that tile.
        # More specifically, it contains information about its "world," "sector,"
        # "arena," "game_object," "spawning_location," as well as whether it is a
        # collision block, and a set of all events taking place in it.
        # e.g., self.tiles[32][59] = {'world': 'double studio',
        #            'sector': '', 'arena': '', 'game_object': '',
        #            'spawning_location': '', 'collision': False, 'events': set()}
        # e.g., self.tiles[9][58] = {'world': 'double studio',
        #         'sector': 'double studio', 'arena': 'bedroom 2',
        #         'game_object': 'bed', 'spawning_location': 'bedroom-2-a',
        #         'collision': False,
        #         'events': {('double studio:double studio:bedroom 2:bed',
        #                    None, None)}}
        self.tiles = []
        for i in range(self.maze_height):
            row = []
            for j in range(self.maze_width):
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
                if self.collision_maze[i][j] != "0":
                    tile_details["collision"] = True

                tile_details["events"] = set()

                row += [tile_details]
            self.tiles += [row]
        # Each game object occupies an event in the tile. We are setting up the
        # default event value here.
        for i in range(self.maze_height):
            for j in range(self.maze_width):
                if self.tiles[i][j]["game_object"]:
                    object_name = ":".join([self.tiles[i][j]["world"],
                                            self.tiles[i][j]["sector"],
                                            self.tiles[i][j]["arena"],
                                            self.tiles[i][j]["game_object"]])
                    go_event = (object_name, None, None, None)
                    self.tiles[i][j]["events"].add(go_event)

        # Reverse tile access.
        # <self.address_tiles> -- given a string address, we return a set of all
        # tile coordinates belonging to that address (this is opposite of
        # self.tiles that give you the string address given a coordinate). This is
        # an optimization component for finding paths for the personas' movement.
        # self.address_tiles['<spawn_loc>bedroom-2-a'] == {(58, 9)}
        # self.address_tiles['double studio:recreation:pool table']
        #   == {(29, 14), (31, 11), (30, 14), (32, 11), ...},
        self.address_tiles = dict()
        for i in range(self.maze_height):
            for j in range(self.maze_width):
                addresses = []
                if self.tiles[i][j]["sector"]:
                    add = f'{self.tiles[i][j]["world"]}:'
                    add += f'{self.tiles[i][j]["sector"]}'
                    addresses += [add]
                if self.tiles[i][j]["arena"]:
                    add = f'{self.tiles[i][j]["world"]}:'
                    add += f'{self.tiles[i][j]["sector"]}:'
                    add += f'{self.tiles[i][j]["arena"]}'
                    addresses += [add]
                if self.tiles[i][j]["game_object"]:
                    add = f'{self.tiles[i][j]["world"]}:'
                    add += f'{self.tiles[i][j]["sector"]}:'
                    add += f'{self.tiles[i][j]["arena"]}:'
                    add += f'{self.tiles[i][j]["game_object"]}'
                    addresses += [add]
                if self.tiles[i][j]["spawning_location"]:
                    add = f'<spawn_loc>{self.tiles[i][j]["spawning_location"]}'
                    addresses += [add]

                for add in addresses:
                    if add in self.address_tiles:
                        self.address_tiles[add].add((j, i))
                    else:
                        self.address_tiles[add] = set([(j, i)])

        # Build an nx.Graph.
        grid_graph = nx.grid_2d_graph(m=self.maze_width, n=self.maze_height)
        for i in range(self.maze_height):
            for j in range(self.maze_width):
                if self.collision_maze[i][j] != 0:
                    grid_graph.remove_node((i, j))
        self.nx_graph = grid_graph

    def turn_coordinate_to_tile(self, px_coordinate: tuple[int, int]) -> tuple[int, int]:
        """
        Turns a pixel coordinate to a tile coordinate.

        INPUT
          px_coordinate: The pixel coordinate of our interest. Comes in the x, y
                         format.
        OUTPUT
          tile coordinate (x, y): The tile coordinate that corresponds to the
                                  pixel coordinate.
        EXAMPLE OUTPUT
          Given (1600, 384), outputs (50, 12)
        """
        x = math.ceil(px_coordinate[0] / self.sq_tile_size)
        y = math.ceil(px_coordinate[1] / self.sq_tile_size)
        return (x, y)

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

    def turn_event_from_tile_idle(self, curr_event: tuple[str], tile: tuple[int, int]) -> None:
        curr_tile_ev_cp = self.tiles[tile[1]][tile[0]]["events"].copy()
        for event in curr_tile_ev_cp:
            if event == curr_event:
                self.tiles[tile[1]][tile[0]]["events"].remove(event)
                new_event = (event[0], None, None, None)
                self.tiles[tile[1]][tile[0]]["events"].add(new_event)

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

    def _find_closest_node(self, coords: tuple[int, int]) -> tuple[int, int]:
        target_coords = self.nx_graph.nodes
        min_dist = None
        closest_coordinate = None
        for target in target_coords:
            dist = math.dist(coords, target)
            if not closest_coordinate:
                min_dist = dist
                closest_coordinate = target
            else:
                if min_dist > dist:
                    min_dist = dist
                    closest_coordinate = target
        return closest_coordinate

    def find_path(self, start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
        if start not in self.nx_graph.nodes:
            start = self._find_closest_node(start)
        if end not in self.nx_graph.nodes:
            end = self._find_closest_node(end)
        return nx.shortest_path(self.nx_graph, start, end)
