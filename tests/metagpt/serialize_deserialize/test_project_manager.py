# -*- coding: utf-8 -*-
# @Date    : 11/26/2023 2:06 PM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import pytest

from metagpt.actions.action import Action
from metagpt.actions.project_management import WriteTasks
from metagpt.roles.project_manager import ProjectManager


def test_project_manager_serialize():
    role = ProjectManager()
    ser_role_dict = role.model_dump(by_alias=True)
    assert "name" in ser_role_dict
    assert "states" in ser_role_dict
    assert "actions" in ser_role_dict


@pytest.mark.asyncio
@pytest.mark.usefixtures("llm_mock")
async def test_project_manager_deserialize():
    role = ProjectManager()
    ser_role_dict = role.model_dump(by_alias=True)

    new_role = ProjectManager(**ser_role_dict)
    assert new_role.name == "Eve"
    assert len(new_role.actions) == 1
    assert isinstance(new_role.actions[0], Action)
    assert isinstance(new_role.actions[0], WriteTasks)
    # await new_role.actions[0].run(context="write a cli snake game")
