# -*- coding: utf-8 -*-
# @Date    : 11/23/2023 4:49 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import pytest

from metagpt.roles.role import Role
from metagpt.roles.engineer import Engineer

from metagpt.actions.action import Action


def test_role_serialize():
    role = Role()
    ser_role_dict = role.dict(by_alias=True)
    assert "name" in ser_role_dict
    assert "_states" in ser_role_dict
    assert "_actions" in ser_role_dict


def test_engineer_serialize():
    role = Engineer()
    ser_role_dict = role.dict(by_alias=True)
    assert "name" in ser_role_dict
    assert "_states" in ser_role_dict
    assert "_actions" in ser_role_dict


@pytest.mark.asyncio
async def test_engineer_deserialize():
    role = Engineer(use_code_review=True)
    ser_role_dict = role.dict(by_alias=True)
    # new_role = Engineer().deserialize(ser_role_dict)
    # also can be deserialized in this way:
    new_role = Engineer(**ser_role_dict)
    assert new_role.name == "Alex"
    assert new_role.use_code_review is True
    assert len(new_role._actions) == 2
    assert isinstance(new_role._actions[0], Action)
    assert isinstance(new_role._actions[1], Action)
    await new_role._actions[0].run(context="write a cli snake game", filename="test_code")
