# -*- coding: utf-8 -*-
# @Date    : 11/26/2023 2:04 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import pytest

from metagpt.roles.architect import Architect
from metagpt.actions.action import Action

def test_architect_serialize():
    role = Architect()
    ser_role_dict = role.dict(by_alias=True)
    assert "name" in ser_role_dict
    assert "_states" in ser_role_dict
    assert "_actions" in ser_role_dict

@pytest.mark.asyncio
async def test_architect_deserialize():
    role = Architect()
    ser_role_dict = role.dict(by_alias=True)
    new_role = Architect(**ser_role_dict)
    # new_role = Architect.deserialize(ser_role_dict)
    assert new_role.name == "Bob"
    assert len(new_role._actions) == 1
    assert isinstance(new_role._actions[0], Action)
    await new_role._actions[0].run(context="write a cli snake game")