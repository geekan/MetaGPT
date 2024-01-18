# -*- coding: utf-8 -*-
# @Desc    :

import pytest

from metagpt.actions import CollectLinks
from metagpt.roles.researcher import Researcher


@pytest.mark.asyncio
async def test_tutorial_assistant_serdeser(context):
    role = Researcher(context=context)
    ser_role_dict = role.model_dump()
    assert "name" in ser_role_dict
    assert "language" in ser_role_dict

    new_role = Researcher(**ser_role_dict, context=context)
    assert new_role.language == "en-us"
    assert len(new_role.actions) == 3
    assert isinstance(new_role.actions[0], CollectLinks)

    # todo: 需要测试不同的action失败下，记忆是否正常保存
