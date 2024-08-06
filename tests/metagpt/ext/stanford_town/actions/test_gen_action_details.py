#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of actions/gen_action_details.py

import pytest

from metagpt.environment import StanfordTownEnv
from metagpt.environment.api.env_api import EnvAPIAbstract
from metagpt.ext.stanford_town.actions.gen_action_details import (
    GenActionArena,
    GenActionDetails,
    GenActionObject,
    GenActionSector,
    GenActObjDescription,
)
from metagpt.ext.stanford_town.roles.st_role import STRole
from metagpt.ext.stanford_town.utils.const import MAZE_ASSET_PATH


@pytest.mark.asyncio
async def test_gen_action_details():
    role = STRole(
        name="Klaus Mueller",
        start_time="February 13, 2023",
        curr_time="February 13, 2023, 00:00:00",
        sim_code="base_the_ville_isabella_maria_klaus",
    )
    role.set_env(StanfordTownEnv(maze_asset_path=MAZE_ASSET_PATH))
    await role.init_curr_tile()

    act_desp = "sleeping"
    act_dura = "120"

    access_tile = await role.rc.env.read_from_api(
        EnvAPIAbstract(api_name="access_tile", kwargs={"tile": role.scratch.curr_tile})
    )
    act_world = access_tile["world"]
    assert act_world == "the Ville"

    sector = await GenActionSector().run(role, access_tile, act_desp)
    arena = await GenActionArena().run(role, act_desp, act_world, sector)
    temp_address = f"{act_world}:{sector}:{arena}"
    obj = await GenActionObject().run(role, act_desp, temp_address)

    act_obj_desp = await GenActObjDescription().run(role, obj, act_desp)

    result_dict = await GenActionDetails().run(role, act_desp, act_dura)

    # gen_action_sector
    assert isinstance(sector, str)
    assert sector in role.s_mem.get_str_accessible_sectors(act_world)

    # gen_action_arena
    assert isinstance(arena, str)
    assert arena in role.s_mem.get_str_accessible_sector_arenas(f"{act_world}:{sector}")

    # gen_action_obj
    assert isinstance(obj, str)
    assert obj in role.s_mem.get_str_accessible_arena_game_objects(temp_address)

    if result_dict:
        for key in [
            "action_address",
            "action_duration",
            "action_description",
            "action_pronunciatio",
            "action_event",
            "chatting_with",
            "chat",
            "chatting_with_buffer",
            "chatting_end_time",
            "act_obj_description",
            "act_obj_pronunciatio",
            "act_obj_event",
        ]:
            assert key in result_dict
    assert result_dict["action_address"] == f"{temp_address}:{obj}"
    assert result_dict["action_duration"] == int(act_dura)
    assert result_dict["act_obj_description"] == act_obj_desp
