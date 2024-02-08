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


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
