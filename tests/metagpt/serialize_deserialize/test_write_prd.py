# -*- coding: utf-8 -*-
# @Date    : 11/22/2023 1:47 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :

import pytest

from metagpt.actions import WritePRD
from metagpt.schema import Message


def test_action_serialize():
    action = WritePRD()
    ser_action_dict = action.model_dump()
    assert "name" in ser_action_dict
    assert "llm" not in ser_action_dict  # not export


@pytest.mark.asyncio
@pytest.mark.usefixtures("llm_mock")
async def test_action_deserialize():
    action = WritePRD()
    serialized_data = action.model_dump()
    new_action = WritePRD(**serialized_data)
    assert new_action.name == "WritePRD"
    action_output = await new_action.run(with_messages=Message(content="write a cli snake game"))
    assert len(action_output.content) > 0
