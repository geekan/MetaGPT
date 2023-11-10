#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/15 11:40
@Author  : alexanderwu
@File    : test_software_company.py
"""
import pytest

from metagpt.logs import logger
from metagpt.team import Team


@pytest.mark.asyncio
async def test_team():
    company = Team()
    company.start_project("做一个基础搜索引擎，可以支持知识库")
    history = await company.run(n_round=5)
    logger.info(history)
