# -*- coding: utf-8 -*-
# @Desc    :
import pytest

from metagpt.roles.sk_agent import SkAgent


@pytest.mark.asyncio
async def test_sk_agent_serdeser():
    role = SkAgent()
    ser_role_dict = role.model_dump(exclude={"import_semantic_skill_from_directory", "import_skill"})
    assert "name" in ser_role_dict
    assert "planner" in ser_role_dict

    new_role = SkAgent(**ser_role_dict)
    assert new_role.name == "Sunshine"
    assert len(new_role.actions) == 1
