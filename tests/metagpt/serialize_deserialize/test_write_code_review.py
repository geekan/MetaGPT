#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of WriteCodeReview SerDeser

import pytest

from metagpt.actions import WriteCodeReview
from metagpt.llm import LLM
from metagpt.schema import CodingContext, Document


def test_write_task_serialize():
    action = WriteCodeReview()
    ser_action_dict = action.dict()
    assert ser_action_dict["name"] == "WriteCodeReview"
    # assert "llm" in ser_action_dict  # not export


@pytest.mark.asyncio
async def test_write_code_review_deserialize():
    code_content = """
def div(a: int, b: int = 0):
    return a / b
"""
    context = CodingContext(
        filename="test_op.py",
        design_doc=Document(content="divide two numbers"),
        code_doc=Document(content=code_content)
    )

    action = WriteCodeReview(context=context)
    serialized_data = action.dict()
    new_action = WriteCodeReview(**serialized_data)

    assert new_action.name == "WriteCodeReview"
    assert new_action.llm == LLM()
    await new_action.run()
