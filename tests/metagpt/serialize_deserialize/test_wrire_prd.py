# -*- coding: utf-8 -*-
# @Date    : 11/22/2023 1:47 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import pytest

from metagpt.actions import WritePRD
from metagpt.llm import LLM
from metagpt.schema import Message


def test_action_serialize():
    action = WritePRD()
    ser_action_dict = action.dict()
    assert "name" in ser_action_dict
    assert "llm" in ser_action_dict


@pytest.mark.asyncio
async def test_action_deserialize():
    action = WritePRD()
    serialized_data = action.dict()
    new_action = WritePRD(**serialized_data)
    assert new_action.name == ""
    assert new_action.llm == LLM()
    action_output = await new_action.run([Message(content="write a cli snake game")])
    assert len(action_output.content) > 0
