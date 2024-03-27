#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of STRole

import pytest

from examples.stanford_town.memory.agent_memory import BasicMemory
from examples.stanford_town.roles.st_role import STRole
from examples.stanford_town.utils.const import MAZE_ASSET_PATH
from metagpt.environment.stanford_town.stanford_town_env import StanfordTownEnv


@pytest.mark.asyncio
async def test_observe():
    role = STRole(
        sim_code="base_the_ville_isabella_maria_klaus",
        start_time="February 13, 2023",
        curr_time="February 13, 2023, 00:00:00",
    )
    role.set_env(StanfordTownEnv(maze_asset_path=MAZE_ASSET_PATH))
    await role.init_curr_tile()

    ret_events = await role.observe()
    assert ret_events
    for event in ret_events:
        assert isinstance(event, BasicMemory)
