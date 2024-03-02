#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : test_write_prd.py
@Modified By: mashenquan, 2023-11-1. According to Chapter 2.2.1 and 2.2.2 of RFC 116, replace `handle` with `run`.
"""

import pytest

from metagpt.actions import UserRequirement, WritePRD
from metagpt.const import REQUIREMENT_FILENAME
from metagpt.logs import logger
from metagpt.roles.product_manager import ProductManager
from metagpt.roles.role import RoleReactMode
from metagpt.schema import Message
from metagpt.utils.common import any_to_str
from tests.data.incremental_dev_project.mock import NEW_REQUIREMENT_SAMPLE, PRD_SAMPLE
from tests.metagpt.actions.test_write_code import setup_inc_workdir


@pytest.mark.asyncio
async def test_write_prd(new_filename, context):
    product_manager = ProductManager(context=context)
    requirements = "开发一个基于大语言模型与私有知识库的搜索引擎，希望可以基于大语言模型进行搜索总结"
    await context.repo.docs.save(filename=REQUIREMENT_FILENAME, content=requirements)
    product_manager.rc.react_mode = RoleReactMode.BY_ORDER
    prd = await product_manager.run(Message(content=requirements, cause_by=UserRequirement))
    assert prd.cause_by == any_to_str(WritePRD)
    logger.info(requirements)
    logger.info(prd)

    # Assert the prd is not None or empty
    assert prd is not None
    assert prd.content != ""
    assert product_manager.context.repo.docs.prd.changed_files


@pytest.mark.asyncio
async def test_write_prd_inc(new_filename, context, git_dir):
    context = setup_inc_workdir(context, inc=True)
    await context.repo.docs.prd.save("1.txt", PRD_SAMPLE)
    await context.repo.docs.save(filename=REQUIREMENT_FILENAME, content=NEW_REQUIREMENT_SAMPLE)

    action = WritePRD(context=context)
    prd = await action.run(Message(content=NEW_REQUIREMENT_SAMPLE, instruct_content=None))
    logger.info(NEW_REQUIREMENT_SAMPLE)
    logger.info(prd)

    # Assert the prd is not None or empty
    assert prd is not None
    assert prd.content != ""
    assert "Refined Requirements" in prd.content


@pytest.mark.asyncio
async def test_fix_debug(new_filename, context, git_dir):
    context.src_workspace = context.git_repo.workdir / context.git_repo.workdir.name

    await context.repo.with_src_path(context.src_workspace).srcs.save(
        filename="main.py", content='if __name__ == "__main__":\nmain()'
    )
    requirements = "Please fix the bug in the code."
    await context.repo.docs.save(filename=REQUIREMENT_FILENAME, content=requirements)
    action = WritePRD(context=context)

    prd = await action.run(Message(content=requirements, instruct_content=None))
    logger.info(prd)

    # Assert the prd is not None or empty
    assert prd is not None
    assert prd.content != ""


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
