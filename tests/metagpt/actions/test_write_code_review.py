#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : test_write_code_review.py
"""
import pytest

from metagpt.actions.write_code_review import WriteCodeReview
from metagpt.schema import CodingContext, Document


@pytest.mark.asyncio
@pytest.mark.usefixtures("llm_mock")
async def test_write_code_review(capfd):
    code = """
def add(a, b):
    return a + 
"""
    context = CodingContext(
        filename="math.py", design_doc=Document(content="编写一个从a加b的函数，返回a+b"), code_doc=Document(content=code)
    )

    context = await WriteCodeReview(context=context).run()

    # 我们不能精确地预测生成的代码评审，但我们可以检查返回的是否为字符串
    assert isinstance(context.code_doc.content, str)
    assert len(context.code_doc.content) > 0

    captured = capfd.readouterr()
    print(f"输出内容: {captured.out}")


# @pytest.mark.asyncio
# async def test_write_code_review_directly():
#     code = SEARCH_CODE_SAMPLE
#     write_code_review = WriteCodeReview("write_code_review")
#     review = await write_code_review.run(code)
#     logger.info(review)
