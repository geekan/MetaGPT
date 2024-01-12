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
from metagpt.context import CONTEXT
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.utils.project_repo import ProjectRepo


@pytest.mark.asyncio
async def test_design_api():
    inputs = ["我们需要一个音乐播放器，它应该有播放、暂停、上一曲、下一曲等功能。"]  # PRD_SAMPLE
    project_repo = ProjectRepo(CONTEXT.git_repo)
    for prd in inputs:
        await project_repo.docs.prd.save(filename="new_prd.txt", content=prd)

        design_api = WriteDesign()

        result = await design_api.run(Message(content=prd, instruct_content=None))
        logger.info(result)

        assert result
