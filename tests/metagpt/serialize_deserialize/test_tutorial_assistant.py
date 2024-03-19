# -*- coding: utf-8 -*-
# @Desc    :
import pytest

from metagpt.actions.write_tutorial import WriteDirectory
from metagpt.roles.tutorial_assistant import TutorialAssistant


@pytest.mark.asyncio
async def test_tutorial_assistant_serdeser(context):
    role = TutorialAssistant()
    ser_role_dict = role.model_dump()
    assert "name" in ser_role_dict
    assert "language" in ser_role_dict
    assert "topic" in ser_role_dict

    new_role = TutorialAssistant(**ser_role_dict)
    assert new_role.name == "Stitch"
    assert len(new_role.actions) == 1
    assert isinstance(new_role.actions[0], WriteDirectory)
