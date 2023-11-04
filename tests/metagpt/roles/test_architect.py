#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/20 14:37
@Author  : alexanderwu
@File    : test_architect.py
@Modified By: mashenquan, 2023-11-1. In accordance with Chapter 2.2.1 and 2.2.2 of RFC 116, utilize the new message
        distribution feature for message handling.
"""
import pytest

from metagpt.logs import logger
from metagpt.roles import Architect
from tests.metagpt.roles.mock import MockMessages


@pytest.mark.asyncio
async def test_architect():
    role = Architect()
    role.put_message(MockMessages.req)
    rsp = await role.run(MockMessages.prd)
    logger.info(rsp)
    assert len(rsp.content) > 0
