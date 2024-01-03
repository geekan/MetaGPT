# -*- coding: utf-8 -*-
# @Date    : 11/22/2023 11:48 AM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import pytest

from metagpt.actions import Action
from metagpt.llm import LLM


def test_action_serialize():
    action = Action()
    ser_action_dict = action.model_dump()
    assert "name" in ser_action_dict
    assert "llm" not in ser_action_dict  # not export
    assert "__module_class_name" not in ser_action_dict

    action = Action(name="test")
    ser_action_dict = action.model_dump()
    assert "test" in ser_action_dict["name"]


@pytest.mark.asyncio
@pytest.mark.usefixtures("llm_mock")
async def test_action_deserialize():
    action = Action()
    serialized_data = action.model_dump()

    new_action = Action(**serialized_data)

    assert new_action.name == "Action"
    assert isinstance(new_action.llm, type(LLM()))
    assert len(await new_action._aask("who are you")) > 0
