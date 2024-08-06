#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of roles conversation

from typing import Tuple

import pytest

from metagpt.environment import StanfordTownEnv
from metagpt.ext.stanford_town.plan.converse import agent_conversation
from metagpt.ext.stanford_town.roles.st_role import STRole
from metagpt.ext.stanford_town.utils.const import MAZE_ASSET_PATH, STORAGE_PATH
from metagpt.ext.stanford_town.utils.mg_ga_transform import get_reverie_meta
from metagpt.ext.stanford_town.utils.utils import copy_folder


async def init_two_roles(fork_sim_code: str = "base_the_ville_isabella_maria_klaus") -> Tuple["STRole"]:
    sim_code = "unittest_sim"

    copy_folder(str(STORAGE_PATH.joinpath(fork_sim_code)), str(STORAGE_PATH.joinpath(sim_code)))

    reverie_meta = get_reverie_meta(fork_sim_code)
    role_ir_name = "Isabella Rodriguez"
    role_km_name = "Klaus Mueller"

    env = StanfordTownEnv(maze_asset_path=MAZE_ASSET_PATH)

    role_ir = STRole(
        name=role_ir_name,
        sim_code=sim_code,
        profile=role_ir_name,
        step=reverie_meta.get("step"),
        start_time=reverie_meta.get("start_date"),
        curr_time=reverie_meta.get("curr_time"),
        sec_per_step=reverie_meta.get("sec_per_step"),
    )
    role_ir.set_env(env)
    await role_ir.init_curr_tile()

    role_km = STRole(
        name=role_km_name,
        sim_code=sim_code,
        profile=role_km_name,
        step=reverie_meta.get("step"),
        start_time=reverie_meta.get("start_date"),
        curr_time=reverie_meta.get("curr_time"),
        sec_per_step=reverie_meta.get("sec_per_step"),
    )
    role_km.set_env(env)
    await role_km.init_curr_tile()

    return role_ir, role_km


@pytest.mark.asyncio
async def test_agent_conversation():
    role_ir, role_km = await init_two_roles()

    curr_chat = await agent_conversation(role_ir, role_km, conv_rounds=2)
    assert len(curr_chat) % 2 == 0

    meet = False
    for conv in curr_chat:
        if "Valentine's Day party" in conv[1]:
            # conv[0] speaker, conv[1] utterance
            meet = True
    assert meet
