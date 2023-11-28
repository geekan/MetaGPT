# -*- coding: utf-8 -*-
# @Date    : 11/23/2023 10:56 AM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import pytest

from metagpt.actions import WriteCode, WriteCodeReview
from metagpt.llm import LLM


def test_write_design_serialize():
    action = WriteCode()
    ser_action_dict = action.dict()
    assert ser_action_dict["name"] == "WriteCode"
    assert "llm" in ser_action_dict


def test_write_task_serialize():
    action = WriteCodeReview()
    ser_action_dict = action.dict()
    assert ser_action_dict["name"] == "WriteCodeReview"
    assert "llm" in ser_action_dict


@pytest.mark.asyncio
async def test_write_code_deserialize():
    action = WriteCode()
    serialized_data = action.dict()
    new_action = WriteCode(**serialized_data)
    # new_action = WriteCode().deserialize(serialized_data)
    assert new_action.name == "WriteCode"
    assert new_action.llm == LLM()
    await new_action.run(context="write a cli snake game", filename="test_code")


@pytest.mark.asyncio
async def test_write_code_review_deserialize():
    action = WriteCodeReview()
    serialized_data = action.dict()
    new_action = WriteCodeReview(**serialized_data)
    # new_action = WriteCodeReview().deserialize(serialized_data)
    code = await WriteCode().run(context="write a cli snake game", filename="test_code")

    assert new_action.name == "WriteCodeReview"
    assert new_action.llm == LLM()
    await new_action.run(context="write a cli snake game", code =code,  filename="test_rewrite_code")