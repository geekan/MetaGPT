#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:12
@Author  : alexanderwu
@File    : test_project_management.py
"""

import pytest

from metagpt.actions.project_management import WriteTasks
from metagpt.context import CONTEXT
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.utils.project_repo import ProjectRepo
from tests.metagpt.actions.mock_json import DESIGN, PRD


@pytest.mark.asyncio
async def test_design_api():
    project_repo = ProjectRepo(CONTEXT.git_repo)
    await project_repo.docs.prd.save("1.txt", content=str(PRD))
    await project_repo.docs.system_design.save("1.txt", content=str(DESIGN))
    logger.info(CONTEXT.git_repo)

    action = WriteTasks()

    result = await action.run(Message(content="", instruct_content=None))
    logger.info(result)

    assert result
