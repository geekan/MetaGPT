#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:26
@Author  : alexanderwu
@File    : test_design_api.py
"""
import pytest

from metagpt.actions.design_api import WriteDesign
from metagpt.logs import logger
from metagpt.schema import Message
from tests.metagpt.actions.mock import PRD_SAMPLE


@pytest.mark.asyncio
async def test_design_api():
    prd = "我们需要一个音乐播放器，它应该有播放、暂停、上一曲、下一曲等功能。"

    design_api = WriteDesign("design_api")

    result = await design_api.run([Message(content=prd, instruct_content=None)])
    logger.info(result)

    assert result


@pytest.mark.asyncio
async def test_design_api_calculator():
    prd = PRD_SAMPLE

    design_api = WriteDesign("design_api")
    result = await design_api.run([Message(content=prd, instruct_content=None)])
    logger.info(result)

    assert result
