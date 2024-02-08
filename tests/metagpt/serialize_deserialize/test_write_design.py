# -*- coding: utf-8 -*-
# @Date    : 11/22/2023 8:19 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import pytest

from metagpt.actions import WriteDesign, WriteTasks


@pytest.mark.asyncio
async def test_write_design_serialize(context):
    action = WriteDesign(context=context)
    ser_action_dict = action.model_dump()
    assert "name" in ser_action_dict
    assert "llm" not in ser_action_dict  # not export

    new_action = WriteDesign(**ser_action_dict, context=context)
    assert new_action.name == "WriteDesign"
    await new_action.run(with_messages="write a cli snake game")


@pytest.mark.asyncio
async def test_write_task_serialize(context):
    action = WriteTasks(context=context)
    ser_action_dict = action.model_dump()
    assert "name" in ser_action_dict
    assert "llm" not in ser_action_dict  # not export

    new_action = WriteTasks(**ser_action_dict, context=context)
    assert new_action.name == "WriteTasks"
    await new_action.run(with_messages="write a cli snake game")
