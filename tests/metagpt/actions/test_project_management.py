#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:12
@Author  : alexanderwu
@File    : test_project_management.py
"""
import json

import pytest

from metagpt.actions.project_management import WriteTasks
from metagpt.const import METAGPT_ROOT
from metagpt.logs import logger
from metagpt.schema import AIMessage, Message
from metagpt.utils.project_repo import ProjectRepo
from tests.data.incremental_dev_project.mock import (
    REFINED_DESIGN_JSON,
    REFINED_PRD_JSON,
    TASK_SAMPLE,
)
from tests.metagpt.actions.mock_json import DESIGN, PRD


@pytest.mark.asyncio
async def test_task(context):
    # Mock write tasks env
    context.kwargs.project_path = context.config.project_path
    context.kwargs.inc = False
    repo = ProjectRepo(context.kwargs.project_path)
    filename = "1.txt"
    await repo.docs.prd.save(filename=filename, content=str(PRD))
    await repo.docs.system_design.save(filename=filename, content=str(DESIGN))
    kvs = {
        "project_path": context.kwargs.project_path,
        "changed_system_design_filenames": [str(repo.docs.system_design.workdir / filename)],
    }
    instruct_content = AIMessage.create_instruct_value(kvs=kvs, class_name="WriteDesignOutput")

    action = WriteTasks(context=context)
    result = await action.run([Message(content="", instruct_content=instruct_content)])
    logger.info(result)
    assert result
    assert result.instruct_content.changed_task_filenames

    # Mock incremental env
    context.kwargs.inc = True
    await repo.docs.prd.save(filename=filename, content=str(REFINED_PRD_JSON))
    await repo.docs.system_design.save(filename=filename, content=str(REFINED_DESIGN_JSON))
    await repo.docs.task.save(filename=filename, content=TASK_SAMPLE)

    result = await action.run([Message(content="", instruct_content=instruct_content)])
    logger.info(result)
    assert result
    assert result.instruct_content.changed_task_filenames


@pytest.mark.asyncio
async def test_task_api(context):
    action = WriteTasks()
    result = await action.run(design_filename=str(METAGPT_ROOT / "tests/data/system_design.json"))
    assert result
    assert result.content
    m = json.loads(result.content)
    assert m


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
