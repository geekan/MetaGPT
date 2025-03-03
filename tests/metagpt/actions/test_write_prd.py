#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : test_write_prd.py
@Modified By: mashenquan, 2023-11-1. According to Chapter 2.2.1 and 2.2.2 of RFC 116, replace `handle` with `run`.
"""
import uuid
from pathlib import Path

import pytest

from metagpt.actions import UserRequirement, WritePRD
from metagpt.const import DEFAULT_WORKSPACE_ROOT, REQUIREMENT_FILENAME
from metagpt.logs import logger
from metagpt.roles.product_manager import ProductManager
from metagpt.roles.role import RoleReactMode
from metagpt.schema import Message
from metagpt.utils.common import any_to_str
from metagpt.utils.project_repo import ProjectRepo
from tests.data.incremental_dev_project.mock import NEW_REQUIREMENT_SAMPLE


@pytest.mark.asyncio
async def test_write_prd(new_filename, context):
    product_manager = ProductManager(context=context)
    requirements = "开发一个基于大语言模型与私有知识库的搜索引擎，希望可以基于大语言模型进行搜索总结"
    product_manager.rc.react_mode = RoleReactMode.BY_ORDER
    prd = await product_manager.run(Message(content=requirements, cause_by=UserRequirement))
    assert prd.cause_by == any_to_str(WritePRD)
    logger.info(requirements)
    logger.info(prd)

    # Assert the prd is not None or empty
    assert prd is not None
    assert prd.content != ""
    repo = ProjectRepo(context.kwargs.project_path)
    assert repo.docs.prd.changed_files
    repo.git_repo.archive()

    # Mock incremental requirement
    context.config.inc = True
    context.config.project_path = context.kwargs.project_path
    repo = ProjectRepo(context.config.project_path)
    await repo.docs.save(filename=REQUIREMENT_FILENAME, content=NEW_REQUIREMENT_SAMPLE)

    action = WritePRD(context=context)
    prd = await action.run([Message(content=NEW_REQUIREMENT_SAMPLE, instruct_content=None)])
    logger.info(NEW_REQUIREMENT_SAMPLE)
    logger.info(prd)

    # Assert the prd is not None or empty
    assert prd is not None
    assert prd.content != ""
    assert repo.git_repo.changed_files


@pytest.mark.asyncio
async def test_fix_debug(new_filename, context, git_dir):
    # Mock legacy project
    context.kwargs.project_path = str(git_dir)
    repo = ProjectRepo(context.kwargs.project_path)
    repo.with_src_path(git_dir.name)
    await repo.srcs.save(filename="main.py", content='if __name__ == "__main__":\nmain()')
    requirements = "ValueError: undefined variable `st`."
    await repo.docs.save(filename=REQUIREMENT_FILENAME, content=requirements)

    action = WritePRD(context=context)
    prd = await action.run([Message(content=requirements, instruct_content=None)])
    logger.info(prd)

    # Assert the prd is not None or empty
    assert prd is not None
    assert prd.content != ""


@pytest.mark.asyncio
async def test_write_prd_api(context):
    action = WritePRD()
    result = await action.run(user_requirement="write a snake game.")
    assert isinstance(result, str)
    assert result
    assert str(DEFAULT_WORKSPACE_ROOT) in result

    result = await action.run(
        user_requirement="write a snake game.",
        output_pathname=str(Path(context.config.project_path) / f"{uuid.uuid4().hex}.json"),
    )
    assert isinstance(result, str)
    assert result
    assert str(context.config.project_path) in result

    ix = result.find(":")
    legacy_prd_filename = result[ix + 1 :].replace('"', "").strip()

    result = await action.run(user_requirement="Add moving enemy.", legacy_prd_filename=legacy_prd_filename)
    assert isinstance(result, str)
    assert result
    assert str(DEFAULT_WORKSPACE_ROOT) in result

    result = await action.run(
        user_requirement="Add moving enemy.",
        output_pathname=str(Path(context.config.project_path) / f"{uuid.uuid4().hex}.json"),
        legacy_prd_filename=legacy_prd_filename,
    )
    assert isinstance(result, str)
    assert result
    assert str(context.config.project_path) in result


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
