#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/16 14:50
@Author  : alexanderwu
@File    : test_product_manager.py
"""
import pytest

from metagpt.logs import logger
from metagpt.roles import ProductManager
from tests.metagpt.roles.mock import MockMessages


@pytest.mark.asyncio
@pytest.mark.usefixtures("llm_mock")
async def test_product_manager():
    product_manager = ProductManager()
    rsp = await product_manager.run(MockMessages.req)
    logger.info(rsp)
    assert len(rsp.content) > 0
    assert rsp.content == MockMessages.req.content
