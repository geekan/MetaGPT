# -*- coding: utf-8 -*-
# @Date    : 11/27/2023 10:07 AM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import pytest

from metagpt.environment import Environment
from metagpt.schema import Message
from metagpt.software_company import SoftwareCompany
from metagpt.roles import ProjectManager, ProductManager, Architect


def test_env_serialize():
    env = Environment()
    ser_env_dict = env.dict()
    assert "roles" in ser_env_dict
    assert "memory" in ser_env_dict
    assert "memory" in ser_env_dict


def test_env_deserialize():
    env = Environment()
    env.publish_message(message=Message(content="test env serialize"))
    ser_env_dict = env.dict()
    new_env = Environment(**ser_env_dict)
    assert len(new_env.roles) == 0
    assert new_env.memory.storage[0].content == "test env serialize"
    assert len(new_env.history) == 25


def test_softwarecompany_deserialize():
    team = SoftwareCompany()
    team.hire(
        [
            ProductManager(),
            Architect(),
            ProjectManager(),
        ]
    )
    assert len(team.environment.get_roles()) == 3
    ser_team_dict = team.dict()
    new_team = SoftwareCompany(**ser_team_dict)
    
    assert len(new_team.environment.get_roles()) == 3
    assert new_team.environment.get_role('Product Manager') is not None
    assert new_team.environment.get_role('Product Manager') is not None
    assert new_team.environment.get_role('Architect') is not None
