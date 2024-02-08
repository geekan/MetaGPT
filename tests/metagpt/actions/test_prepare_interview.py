#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/13 00:26
@Author  : fisherdeng
@File    : test_generate_questions.py
"""
import pytest

from metagpt.actions.prepare_interview import PrepareInterview
from metagpt.logs import logger


@pytest.mark.asyncio
async def test_prepare_interview(context):
    action = PrepareInterview(context=context)
    rsp = await action.run("I just graduated and hope to find a job as a Python engineer")
    logger.info(f"{rsp.content=}")

    assert "Questions" in rsp.content
    assert "1." in rsp.content
