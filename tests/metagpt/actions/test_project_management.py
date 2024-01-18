#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:12
@Author  : alexanderwu
@File    : test_project_management.py
"""

import pytest

from metagpt.actions.project_management import WriteTasks
from metagpt.logs import logger
from metagpt.schema import Message
from tests.metagpt.actions.mock_json import DESIGN, PRD


@pytest.mark.asyncio
async def test_design_api(context):
    await context.repo.docs.prd.save("1.txt", content=str(PRD))
    await context.repo.docs.system_design.save("1.txt", content=str(DESIGN))
    logger.info(context.git_repo)

    action = WriteTasks(context=context)

    result = await action.run(Message(content="", instruct_content=None))
    logger.info(result)

    assert result
