# -*- coding: utf-8 -*-
# @Date    : 11/26/2023 2:04 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import pytest

from metagpt.actions.action import Action
from metagpt.roles.architect import Architect


def test_architect_serialize():
    role = Architect()
    ser_role_dict = role.model_dump(by_alias=True)
    assert "name" in ser_role_dict
    assert "states" in ser_role_dict
    assert "actions" in ser_role_dict


@pytest.mark.asyncio
@pytest.mark.usefixtures("llm_mock")
async def test_architect_deserialize():
    role = Architect()
    ser_role_dict = role.model_dump(by_alias=True)
    new_role = Architect(**ser_role_dict)
    # new_role = Architect.deserialize(ser_role_dict)
    assert new_role.name == "Bob"
    assert len(new_role.actions) == 1
    assert isinstance(new_role.actions[0], Action)
    await new_role.actions[0].run(with_messages="write a cli snake game")
