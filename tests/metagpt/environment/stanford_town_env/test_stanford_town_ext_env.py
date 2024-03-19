#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of StanfordTownExtEnv

from pathlib import Path

from metagpt.environment.stanford_town_env.stanford_town_ext_env import (
    StanfordTownExtEnv,
)

maze_asset_path = (
    Path(__file__).absolute().parent.joinpath("..", "..", "..", "data", "environment", "stanford_town", "the_ville")
)


def test_stanford_town_ext_env():
    ext_env = StanfordTownExtEnv(maze_asset_path=maze_asset_path)

    tile_coord = ext_env.turn_coordinate_to_tile((64, 64))
    assert tile_coord == (2, 2)

    tile = (58, 9)
    assert len(ext_env.get_collision_maze()) == 100
    assert len(ext_env.get_address_tiles()) == 306
    assert ext_env.access_tile(tile=tile)["world"] == "the Ville"
    assert ext_env.get_tile_path(tile=tile, level="world") == "the Ville"
    assert len(ext_env.get_nearby_tiles(tile=tile, vision_r=5)) == 121

    event = ("double studio:double studio:bedroom 2:bed", None, None, None)
    ext_env.add_tiles_event(tile[1], tile[0], event=event)
    ext_env.add_event_from_tile(event, tile)
    assert len(ext_env.tiles[tile[1]][tile[0]]["events"]) == 1

    ext_env.turn_event_from_tile_idle(event, tile)

    ext_env.remove_event_from_tile(event, tile)
    assert len(ext_env.tiles[tile[1]][tile[0]]["events"]) == 0

    ext_env.remove_subject_events_from_tile(subject=event[0], tile=tile)
    assert len(ext_env.tiles[tile[1]][tile[0]]["events"]) == 0
