#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/15 11:40
@Author  : alexanderwu
@File    : test_startup.py
"""
import pytest
from typer.testing import CliRunner

from metagpt.logs import logger
from metagpt.startup import app
from metagpt.team import Team

runner = CliRunner()


@pytest.mark.asyncio
async def test_empty_team():
    # FIXME: we're now using "metagpt" cli, so the entrance should be replaced instead.
    company = Team()
    history = await company.run(idea="Build a simple search system. I will upload my files later.")
    logger.info(history)


def test_startup():
    args = ["Make a 2048 game"]
    result = runner.invoke(app, args)
    logger.info(result)


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
