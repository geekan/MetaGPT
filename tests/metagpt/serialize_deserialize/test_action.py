# -*- coding: utf-8 -*-
# @Date    : 11/22/2023 11:48 AM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import pytest

from metagpt.actions import Action, WritePRD, WriteTest
from metagpt.llm import LLM
from metagpt.provider.openai_api import OpenAIGPTAPI


def test_action_serialize():
    action = Action()
    ser_action_dict = action.dict()
    assert "name" in ser_action_dict
    assert "llm" not in ser_action_dict


@pytest.mark.asyncio
async def test_action_deserialize():
    action = Action()
    serialized_data = action.dict()

    new_action = Action(**serialized_data)

    assert new_action.name == ""
    assert new_action.llm == LLM()
    assert len(await new_action._aask("who are you")) > 0


def test_action_serdeser():
    action_info = WriteTest.ser_class()
    assert action_info["action_class"] == "WriteTest"

    action_class = Action.deser_class(action_info)
    assert action_class == WriteTest


def test_action_class_serdeser():
    name = "write test"
    action_info = WriteTest(name=name).serialize()
    assert action_info["name"] == name

    action_info = WriteTest(name=name, llm=LLM()).serialize()
    assert action_info["name"] == name

    action = Action.deserialize(action_info)
    assert action.name == name
