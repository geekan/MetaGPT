#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of WriteCodeReview SerDeser

import pytest

from metagpt.actions import WriteCodeReview
from metagpt.schema import CodingContext, Document


@pytest.mark.asyncio
async def test_write_code_review_serdeser(context):
    context.src_workspace = context.repo.workdir / "srcs"
    code_content = """
def div(a: int, b: int = 0):
    return a / b
"""
    coding_context = CodingContext(
        filename="test_op.py",
        design_doc=Document(content="divide two numbers"),
        code_doc=Document(content=code_content),
    )

    action = WriteCodeReview(i_context=coding_context)
    serialized_data = action.model_dump()
    assert serialized_data["name"] == "WriteCodeReview"

    new_action = WriteCodeReview(**serialized_data, context=context)

    assert new_action.name == "WriteCodeReview"
    await new_action.run()
