# -*- coding: utf-8 -*-
# @Date    : 11/26/2023 2:06 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import pytest

from metagpt.actions.action import Action
from metagpt.actions.project_management import WriteTasks
from metagpt.roles.project_manager import ProjectManager


@pytest.mark.asyncio
async def test_project_manager_serdeser(context):
    role = ProjectManager(context=context)
    ser_role_dict = role.model_dump(by_alias=True)
    assert "name" in ser_role_dict
    assert "states" in ser_role_dict
    assert "actions" in ser_role_dict

    new_role = ProjectManager(**ser_role_dict, context=context)
    assert new_role.name == "Eve"
    assert len(new_role.actions) == 1
    assert isinstance(new_role.actions[0], Action)
    assert isinstance(new_role.actions[0], WriteTasks)
    # await new_role.actions[0].run(context="write a cli snake game")
