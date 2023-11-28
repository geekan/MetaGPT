# -*- coding: utf-8 -*-
# @Date    : 11/22/2023 11:48 AM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import pytest

from metagpt.actions import Action
from metagpt.llm import LLM


def test_action_serialize():
    action = Action()
    ser_action_dict = action.dict()
    assert "name" in ser_action_dict
    assert "llm" in ser_action_dict


@pytest.mark.asyncio
async def test_action_deserialize():
    action = Action()
    serialized_data = action.dict()
    
    new_action = Action(**serialized_data)
    assert new_action.name == ""
    assert new_action.llm == LLM()
    assert len(await new_action._aask("who are you")) > 0
