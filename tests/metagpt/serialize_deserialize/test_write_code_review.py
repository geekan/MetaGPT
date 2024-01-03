#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of WriteCodeReview SerDeser

import pytest

from metagpt.actions import WriteCodeReview
from metagpt.schema import CodingContext, Document


@pytest.mark.asyncio
@pytest.mark.usefixtures("llm_mock")
async def test_write_code_review_deserialize():
    code_content = """
def div(a: int, b: int = 0):
    return a / b
"""
    context = CodingContext(
        filename="test_op.py",
        design_doc=Document(content="divide two numbers"),
        code_doc=Document(content=code_content),
    )

    action = WriteCodeReview(context=context)
    serialized_data = action.model_dump()
    assert serialized_data["name"] == "WriteCodeReview"

    new_action = WriteCodeReview(**serialized_data)

    assert new_action.name == "WriteCodeReview"
    await new_action.run()
