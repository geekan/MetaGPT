#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/20 14:37
@Author  : alexanderwu
@File    : test_architect.py
"""
import pytest

from metagpt.actions import BossRequirement
from metagpt.logs import logger
from metagpt.roles import Architect
from metagpt.schema import Message
from tests.metagpt.roles.mock import PRD, DETAIL_REQUIREMENT, BOSS_REQUIREMENT, MockMessages


@pytest.mark.asyncio
async def test_architect():
    role = Architect()
    role.recv(MockMessages.req)
    rsp = await role.handle(MockMessages.prd)
    logger.info(rsp)
    assert len(rsp.content) > 0
