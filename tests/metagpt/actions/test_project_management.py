#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:12
@Author  : alexanderwu
@File    : test_project_management.py
"""

import pytest

from metagpt.actions.project_management import WriteTasks
from metagpt.config import CONFIG
from metagpt.const import PRDS_FILE_REPO, SYSTEM_DESIGN_FILE_REPO
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.utils.file_repository import FileRepository
from tests.metagpt.actions.mock_json import DESIGN, PRD


@pytest.mark.asyncio
@pytest.mark.usefixtures("llm_mock")
async def test_design_api():
    await FileRepository.save_file("1.txt", content=str(PRD), relative_path=PRDS_FILE_REPO)
    await FileRepository.save_file("1.txt", content=str(DESIGN), relative_path=SYSTEM_DESIGN_FILE_REPO)
    logger.info(CONFIG.git_repo)

    action = WriteTasks()

    result = await action.run(Message(content="", instruct_content=None))
    logger.info(result)

    assert result
