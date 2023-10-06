#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of actions/gen_action_details.py

from examples.st_game.actions.gen_action_details import (
    GenActionDetails,
    GenActionArena,
    GenActionSector,
    GenActionObject,
    GenActObjDescription,
    GenEventTriple,
    GenObjEventTriple,
    GenPronunciatio 
    )
from examples.st_game.roles.st_role import STRole

role = STRole(name="Klaus Mueller", start_date="October 4, 2023", curr_time="October 4, 2023, 00:00:00", 
                sim_code="base_the_ville_isabella_maria_klaus")
maze = role._rc.env.maze
act_desp = "klaus mueller starts the day by making a coffee"
act_dura = "20"
act_world = maze.access_tile(role.scratch.curr_tile)["world"]
assert act_world == "the Ville"

sector = GenActionSector().run(role, maze, act_desp)
arena = GenActionArena().run(role, maze, act_desp, act_world, sector)
temp_address = f"{act_world}:{sector}:{arena}"
obj = GenActionObject().run(role, act_desp, temp_address)

act_obj_desp = GenActObjDescription().run(role, obj, act_desp)
# event_triple = GenEventTriple().run(role, act_desp)
# obj_triple = GenObjEventTriple().run(role, obj, act_obj_desp)

result_dict = GenActionDetails().run(role, act_desp, act_dura)

def test_gen_action_sector():
    assert isinstance(sector, str)
    assert sector in role.s_mem.get_str_accessible_sectors(act_world)

def test_gen_action_arena():
    assert isinstance(arena, str)
    assert arena in role.s_mem.get_str_accessible_sector_arenas(f"{act_world}:{sector}")

def test_gen_action_obj():
    assert isinstance(obj, str)
    assert obj in role.s_mem.get_str_accessible_arena_game_objects(temp_address)

# def test_gen_event_triple():
#     assert len(event_triple) == 3

# def test_gen_obj_event_triple():
#     assert len(obj_triple) == 3

def test_gen_action_details():
    if result_dict:
        for key in [
            "action_address",
            "action_duration",
            "act_desp",
            "action_pronunciatio",
            "action_event",
            "chatting_with",
            "chat",
            "chatting_with_buffer",
            "chatting_end_time",
            "act_obj_description",
            "act_obj_pronunciatio",
            "act_obj_event"]:
            assert key in result_dict
    assert result_dict["action_address"] == f"{temp_address}:{obj}"
    assert result_dict["action_duration"] == int(act_dura)
    assert result_dict["act_obj_description"] == act_obj_desp
    