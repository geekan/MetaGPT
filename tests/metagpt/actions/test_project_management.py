#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:12
@Author  : alexanderwu
@File    : test_project_management.py
"""

import pytest

from metagpt.actions.project_management import WriteTasks
from metagpt.llm import LLM
from metagpt.logs import logger
from metagpt.schema import Message
from tests.data.incremental_dev_project.mock import (
    REFINED_DESIGN_JSON,
    REFINED_PRD_JSON,
    TASK_SAMPLE,
)
from tests.metagpt.actions.mock_json import DESIGN, PRD


@pytest.mark.asyncio
async def test_task(context):
    await context.repo.docs.prd.save("1.txt", content=str(PRD))
    await context.repo.docs.system_design.save("1.txt", content=str(DESIGN))
    logger.info(context.git_repo)

    action = WriteTasks(context=context)

    result = await action.run(Message(content="", instruct_content=None))
    logger.info(result)

    assert result


@pytest.mark.asyncio
async def test_refined_task(context):
    await context.repo.docs.prd.save("2.txt", content=str(REFINED_PRD_JSON))
    await context.repo.docs.system_design.save("2.txt", content=str(REFINED_DESIGN_JSON))
    await context.repo.docs.task.save("2.txt", content=TASK_SAMPLE)

    logger.info(context.git_repo)

    action = WriteTasks(context=context, llm=LLM())

    result = await action.run(Message(content="", instruct_content=None))
    logger.info(result)

    assert result
