#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/13 00:26
@Author  : fisherdeng
@File    : test_generate_questions.py
"""
import pytest

from metagpt.actions.generate_questions import GenerateQuestions
from metagpt.logs import logger

msg = """
## topic
如何做一个生日蛋糕

## record
我认为应该先准备好材料，然后再开始做蛋糕。
"""


@pytest.mark.asyncio
async def test_generate_questions(context):
    action = GenerateQuestions(context=context)
    rsp = await action.run(msg)
    logger.info(f"{rsp.content=}")

    assert "Questions" in rsp.content
    assert "1." in rsp.content
