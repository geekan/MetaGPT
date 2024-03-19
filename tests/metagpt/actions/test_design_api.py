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
from metagpt.llm import LLM
from metagpt.logs import logger
from metagpt.schema import Message
from tests.data.incremental_dev_project.mock import DESIGN_SAMPLE, REFINED_PRD_JSON


@pytest.mark.asyncio
async def test_design_api(context):
    inputs = ["我们需要一个音乐播放器，它应该有播放、暂停、上一曲、下一曲等功能。"]  # PRD_SAMPLE
    for prd in inputs:
        await context.repo.docs.prd.save(filename="new_prd.txt", content=prd)

        design_api = WriteDesign(context=context)

        result = await design_api.run(Message(content=prd, instruct_content=None))
        logger.info(result)

        assert result


@pytest.mark.asyncio
async def test_refined_design_api(context):
    await context.repo.docs.prd.save(filename="1.txt", content=str(REFINED_PRD_JSON))
    await context.repo.docs.system_design.save(filename="1.txt", content=DESIGN_SAMPLE)

    design_api = WriteDesign(context=context, llm=LLM())

    result = await design_api.run(Message(content="", instruct_content=None))
    logger.info(result)

    assert result
