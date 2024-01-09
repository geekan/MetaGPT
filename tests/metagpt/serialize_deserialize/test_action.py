# -*- coding: utf-8 -*-
# @Date    : 11/22/2023 11:48 AM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import pytest

from metagpt.actions import Action
from metagpt.llm import LLM


@pytest.mark.asyncio
async def test_action_serdeser():
    action = Action()
    ser_action_dict = action.model_dump()
    assert "name" in ser_action_dict
    assert "llm" not in ser_action_dict  # not export
    assert "__module_class_name" in ser_action_dict

    action = Action(name="test")
    ser_action_dict = action.model_dump()
    assert "test" in ser_action_dict["name"]

    new_action = Action(**ser_action_dict)

    assert new_action.name == "test"
    assert isinstance(new_action.llm, type(LLM()))
    assert len(await new_action._aask("who are you")) > 0
