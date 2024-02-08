#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:26
@Author  : alexanderwu
@File    : test_design_api.py
@Modifiled By: mashenquan, 2023-12-6. According to RFC 135
"""
import pytest

from metagpt.actions.design_api import WriteDesign
from metagpt.logs import logger
from metagpt.schema import Message


@pytest.mark.asyncio
async def test_design_api(context):
    inputs = ["我们需要一个音乐播放器，它应该有播放、暂停、上一曲、下一曲等功能。"]  # PRD_SAMPLE
    for prd in inputs:
        await context.repo.docs.prd.save(filename="new_prd.txt", content=prd)

        design_api = WriteDesign(context=context)

        result = await design_api.run(Message(content=prd, instruct_content=None))
        logger.info(result)

        assert result
