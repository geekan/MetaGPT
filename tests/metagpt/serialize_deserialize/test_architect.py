# -*- coding: utf-8 -*-
# @Date    : 11/26/2023 2:04 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import pytest

from metagpt.actions.action import Action
from metagpt.roles.architect import Architect


@pytest.mark.asyncio
async def test_architect_serdeser(context):
    role = Architect(context=context)
    ser_role_dict = role.model_dump(by_alias=True)
    assert "name" in ser_role_dict
    assert "states" in ser_role_dict
    assert "actions" in ser_role_dict

    new_role = Architect(**ser_role_dict, context=context)
    assert new_role.name == "Bob"
    assert len(new_role.actions) == 1
    assert len(new_role.rc.watch) == 1
    assert isinstance(new_role.actions[0], Action)
    await new_role.actions[0].run(with_messages="write a cli snake game")


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
