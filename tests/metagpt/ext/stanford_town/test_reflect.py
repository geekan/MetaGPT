#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of reflection

import pytest

from metagpt.environment import StanfordTownEnv
from metagpt.ext.stanford_town.actions.run_reflect_action import (
    AgentEventTriple,
    AgentFocusPt,
    AgentInsightAndGuidance,
)
from metagpt.ext.stanford_town.roles.st_role import STRole
from metagpt.ext.stanford_town.utils.const import MAZE_ASSET_PATH


@pytest.mark.asyncio
async def test_reflect():
    """
    init STRole form local json, set sim_code(path),curr_time & start_time
    """
    role = STRole(
        sim_code="base_the_ville_isabella_maria_klaus",
        start_time="February 13, 2023",
        curr_time="February 13, 2023, 00:00:00",
    )
    role.set_env(StanfordTownEnv(maze_asset_path=MAZE_ASSET_PATH))
    role.init_curr_tile()

    run_focus = AgentFocusPt()
    statements = ""
    await run_focus.run(role, statements, n=3)

    """
    这里有通过测试的结果，但是更多时候LLM生成的结果缺少了because of；考虑修改一下prompt
    result = {'Klaus Mueller and Maria Lopez have a close relationship because they have been friends for a long time and have a strong bond': [1, 2, 5, 9, 11, 14], 'Klaus Mueller has a crush on Maria Lopez': [8, 15, 24], 'Klaus Mueller is academically inclined and actively researching a topic': [13, 20], 'Klaus Mueller is socially active and acquainted with Isabella Rodriguez': [17, 21, 22], 'Klaus Mueller is organized and prepared': [19]}
    """
    run_insight = AgentInsightAndGuidance()
    statements = "[user: Klaus Mueller has a close relationship with Maria Lopez, user:s Mueller and Maria Lopez have a close relationship, user: Klaus Mueller has a close relationship with Maria Lopez, user: Klaus Mueller has a close relationship with Maria Lopez, user: Klaus Mueller and Maria Lopez have a strong relationship, user: Klaus Mueller is a dormmate of Maria Lopez., user: Klaus Mueller and Maria Lopez have a strong bond, user: Klaus Mueller has a crush on Maria Lopez, user: Klaus Mueller and Maria Lopez have been friends for more than 2 years., user: Klaus Mueller has a close relationship with Maria Lopez, user: Klaus Mueller Maria Lopez is heading off to college., user: Klaus Mueller and Maria Lopez have a close relationship, user: Klaus Mueller is actively researching a topic, user: Klaus Mueller is close friends and classmates with Maria Lopez., user: Klaus Mueller is socially active, user: Klaus Mueller has a crush on Maria Lopez., user: Klaus Mueller and Maria Lopez have been friends for a long time, user: Klaus Mueller is academically inclined, user: For Klaus Mueller's planning: should remember to ask Maria Lopez about her research paper, as she found it interesting that he mentioned it., user: Klaus Mueller is acquainted with Isabella Rodriguez, user: Klaus Mueller is organized and prepared, user: Maria Lopez is conversing about conversing about Maria's research paper mentioned by Klaus, user: Klaus Mueller is conversing about conversing about Maria's research paper mentioned by Klaus, user: Klaus Mueller is a student, user: Klaus Mueller is a student, user: Klaus Mueller is conversing about two friends named Klaus Mueller and Maria Lopez discussing their morning plans and progress on a research paper before Maria heads off to college., user: Klaus Mueller is socially active, user: Klaus Mueller is socially active, user: Klaus Mueller is socially active and acquainted with Isabella Rodriguez, user: Klaus Mueller has a crush on Maria Lopez]"
    await run_insight.run(role, statements, n=5)

    run_triple = AgentEventTriple()
    statements = "(Klaus Mueller is academically inclined)"
    await run_triple.run(statements, role)

    role.scratch.importance_trigger_curr = -1
    role.reflect()
