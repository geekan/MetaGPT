#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : test_write_prd.py
@Modified By: mashenquan, 2023-11-1. According to Chapter 2.2.1 and 2.2.2 of RFC 116, replace `handle` with `run`.
"""
import pytest

from metagpt.actions import UserRequirement
from metagpt.config import CONFIG
from metagpt.const import DOCS_FILE_REPO, PRDS_FILE_REPO, REQUIREMENT_FILENAME
from metagpt.logs import logger
from metagpt.roles.product_manager import ProductManager
from metagpt.schema import Message
from metagpt.utils.file_repository import FileRepository


@pytest.mark.asyncio
@pytest.mark.usefixtures("llm_mock")
async def test_write_prd():
    product_manager = ProductManager()
    requirements = "开发一个基于大语言模型与私有知识库的搜索引擎，希望可以基于大语言模型进行搜索总结"
    await FileRepository.save_file(filename=REQUIREMENT_FILENAME, content=requirements, relative_path=DOCS_FILE_REPO)
    prd = await product_manager.run(Message(content=requirements, cause_by=UserRequirement))
    logger.info(requirements)
    logger.info(prd)

    # Assert the prd is not None or empty
    assert prd is not None
    assert prd.content != ""
    assert CONFIG.git_repo.new_file_repository(relative_path=PRDS_FILE_REPO).changed_files
