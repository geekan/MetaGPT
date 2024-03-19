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
async def test_write_code_review(capfd, context):
    context.src_workspace = context.repo.workdir / "srcs"
    code = """
def add(a, b):
    return a + 
"""
    coding_context = CodingContext(
        filename="math.py", design_doc=Document(content="编写一个从a加b的函数，返回a+b"), code_doc=Document(content=code)
    )

    await WriteCodeReview(i_context=coding_context, context=context).run()

    # 我们不能精确地预测生成的代码评审，但我们可以检查返回的是否为字符串
    assert isinstance(coding_context.code_doc.content, str)
    assert len(coding_context.code_doc.content) > 0

    captured = capfd.readouterr()
    print(f"输出内容: {captured.out}")


@pytest.mark.asyncio
async def test_write_code_review_inc(capfd, context):
    context.src_workspace = context.repo.workdir / "srcs"
    context.config.inc = True
    code = """
    def add(a, b):
        return a + 
    """
    code_plan_and_change = """
    def add(a, b):
-        return a + 
+        return a + b
    """
    coding_context = CodingContext(
        filename="math.py",
        design_doc=Document(content="编写一个从a加b的函数，返回a+b"),
        code_doc=Document(content=code),
        code_plan_and_change_doc=Document(content=code_plan_and_change),
    )

    await WriteCodeReview(i_context=coding_context, context=context).run()


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
