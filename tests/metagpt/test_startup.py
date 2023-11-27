#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/15 11:40
@Author  : alexanderwu
@File    : test_startup.py
"""
import pytest
from typer.testing import CliRunner

runner = CliRunner()

from metagpt.logs import logger
from metagpt.team import Team
from metagpt.startup import app


@pytest.mark.asyncio
async def test_team():
    company = Team()
    company.run_project("做一个基础搜索引擎，可以支持知识库")
    history = await company.run(n_round=5)
    logger.info(history)


# def test_startup():
#     args = ["Make a 2048 game"]
#     result = runner.invoke(app, args)
