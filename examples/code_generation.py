#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from metagpt.logs import logger
from metagpt.roles.engineer import Engineer
from metagpt.utils.common import CodeParser
from mock import (
    TASKS,
    MockMessages,
)

import asyncio

@pytest.mark.asyncio
async def test_engineer():
    engineer = Engineer()

    engineer.recv(MockMessages.req)
    engineer.recv(MockMessages.prd)
    engineer.recv(MockMessages.system_design)
    rsp = await engineer.handle(MockMessages.tasks)

    logger.info(rsp)
    assert "all done." == rsp.content

if __name__ == '__main__':
    asyncio.run(test_engineer())