# -*- coding: utf-8 -*-
# @Date    : 11/22/2023 8:19 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import pytest

from metagpt.actions import WriteDesign, WriteTasks


def test_write_design_serialize():
    action = WriteDesign()
    ser_action_dict = action.model_dump()
    assert "name" in ser_action_dict
    assert "llm" not in ser_action_dict  # not export


def test_write_task_serialize():
    action = WriteTasks()
    ser_action_dict = action.model_dump()
    assert "name" in ser_action_dict
    assert "llm" not in ser_action_dict  # not export


@pytest.mark.asyncio
@pytest.mark.usefixtures("llm_mock")
async def test_write_design_deserialize():
    action = WriteDesign()
    serialized_data = action.model_dump()
    new_action = WriteDesign(**serialized_data)
    assert new_action.name == "WriteDesign"
    await new_action.run(with_messages="write a cli snake game")


@pytest.mark.asyncio
@pytest.mark.usefixtures("llm_mock")
async def test_write_task_deserialize():
    action = WriteTasks()
    serialized_data = action.model_dump()
    new_action = WriteTasks(**serialized_data)
    assert new_action.name == "WriteTasks"
    await new_action.run(with_messages="write a cli snake game")
