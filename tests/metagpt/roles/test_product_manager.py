#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/16 14:50
@Author  : alexanderwu
@File    : test_product_manager.py
"""
import pytest
from metagpt.logs import logger

from metagpt.actions import BossRequirement
from metagpt.roles import ProductManager
from metagpt.schema import Message
from tests.metagpt.roles.mock import DETAIL_REQUIREMENT, BOSS_REQUIREMENT, MockMessages


@pytest.mark.asyncio
async def test_product_manager():
    product_manager = ProductManager()
    rsp = await product_manager.handle(MockMessages.req)
    logger.info(rsp)
    assert len(rsp.content) > 0
    assert "产品目标" in rsp.content
