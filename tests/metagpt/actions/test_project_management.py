#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:12
@Author  : alexanderwu
@File    : test_project_management.py
"""

import pytest

from metagpt.actions.project_management import WriteTasks
from metagpt.const import PRDS_FILE_REPO, SYSTEM_DESIGN_FILE_REPO
from metagpt.context import context
from metagpt.logs import logger
from metagpt.schema import Message
from tests.metagpt.actions.mock_json import DESIGN, PRD


@pytest.mark.asyncio
async def test_design_api():
    await context.file_repo.save_file("1.txt", content=str(PRD), relative_path=PRDS_FILE_REPO)
    await context.file_repo.save_file("1.txt", content=str(DESIGN), relative_path=SYSTEM_DESIGN_FILE_REPO)
    logger.info(context.git_repo)

    action = WriteTasks()

    result = await action.run(Message(content="", instruct_content=None))
    logger.info(result)

    assert result
