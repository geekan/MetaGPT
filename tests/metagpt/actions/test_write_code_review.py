#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : test_write_code_review.py
"""
import pytest
from metagpt.logs import logger
from metagpt.llm import LLM
from metagpt.actions.write_code_review import WriteCodeReview
from tests.metagpt.actions.mock import SEARCH_CODE_SAMPLE


@pytest.mark.asyncio
async def test_write_code_review():
    code = """
def add(a, b):
    return a + b
"""
    write_code_review = WriteCodeReview("write_code_review")

    review = await write_code_review.run(code)

    # 我们不能精确地预测生成的代码评审，但我们可以检查返回的是否为字符串
    assert isinstance(review, str)
    assert len(review) > 0


@pytest.mark.asyncio
async def test_write_code_review_directly():
    code = SEARCH_CODE_SAMPLE
    write_code_review = WriteCodeReview("write_code_review")
    review = await write_code_review.run(code)
    logger.info(review)
