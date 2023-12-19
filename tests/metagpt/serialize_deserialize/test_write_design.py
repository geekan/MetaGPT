# -*- coding: utf-8 -*-
# @Date    : 11/22/2023 8:19 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import pytest

from metagpt.actions import WriteDesign, WriteTasks
from metagpt.llm import LLM


def test_write_design_serialize():
    action = WriteDesign()
    ser_action_dict = action.dict()
    assert "name" in ser_action_dict
    # assert "llm" in ser_action_dict  # not export


def test_write_task_serialize():
    action = WriteTasks()
    ser_action_dict = action.dict()
    assert "name" in ser_action_dict
    # assert "llm" in ser_action_dict  # not export


@pytest.mark.asyncio
async def test_write_design_deserialize():
    action = WriteDesign()
    serialized_data = action.dict()
    new_action = WriteDesign(**serialized_data)
    assert new_action.name == ""
    assert new_action.llm == LLM()
    await new_action.run(with_messages="write a cli snake game")


@pytest.mark.asyncio
async def test_write_task_deserialize():
    action = WriteTasks()
    serialized_data = action.dict()
    new_action = WriteTasks(**serialized_data)
    assert new_action.name == "CreateTasks"
    assert new_action.llm == LLM()
    await new_action.run(with_messages="write a cli snake game")
