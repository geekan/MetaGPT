# -*- coding: utf-8 -*-
# @Date    : 11/27/2023 10:07 AM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :

import shutil

import pytest

from metagpt.const import SERDESER_PATH
from metagpt.logs import logger
from metagpt.roles import Architect, ProductManager, ProjectManager
from metagpt.team import Team
from tests.metagpt.serialize_deserialize.test_serdeser_base import (
    ActionOK,
    RoleA,
    RoleB,
    RoleC,
    serdeser_path,
)


def test_team_deserialize():
    company = Team()

    pm = ProductManager()
    arch = Architect()
    company.hire(
        [
            pm,
            arch,
            ProjectManager(),
        ]
    )
    assert len(company.env.get_roles()) == 3
    ser_company = company.model_dump()
    new_company = Team.model_validate(ser_company)

    assert len(new_company.env.get_roles()) == 3
    assert new_company.env.get_role(pm.profile) is not None

    new_pm = new_company.env.get_role(pm.profile)
    assert type(new_pm) == ProductManager
    assert new_company.env.get_role(pm.profile) is not None
    assert new_company.env.get_role(arch.profile) is not None


def test_team_serdeser_save():
    company = Team()

    company.hire([RoleC()])

    stg_path = serdeser_path.joinpath("team")
    shutil.rmtree(stg_path, ignore_errors=True)

    company.serialize(stg_path=stg_path)

    new_company = Team.deserialize(stg_path)

    assert len(new_company.env.roles) == 1


@pytest.mark.asyncio
async def test_team_recover():
    idea = "write a snake game"
    stg_path = SERDESER_PATH.joinpath("team")
    shutil.rmtree(stg_path, ignore_errors=True)

    company = Team()
    role_c = RoleC()
    company.hire([role_c])
    company.run_project(idea)
    await company.run(n_round=4)

    ser_data = company.model_dump()
    new_company = Team(**ser_data)

    new_company.env.get_role(role_c.profile)
    # assert new_role_c.rc.memory == role_c.rc.memory  # TODO
    # assert new_role_c.rc.env != role_c.rc.env  # TODO
    assert type(list(new_company.env.roles.values())[0].actions[0]) == ActionOK

    new_company.run_project(idea)
    await new_company.run(n_round=4)


@pytest.mark.asyncio
async def test_team_recover_save():
    idea = "write a 2048 web game"
    stg_path = SERDESER_PATH.joinpath("team")
    shutil.rmtree(stg_path, ignore_errors=True)

    company = Team()
    role_c = RoleC()
    company.hire([role_c])
    company.run_project(idea)
    await company.run(n_round=4)

    new_company = Team.deserialize(stg_path)
    new_role_c = new_company.env.get_role(role_c.profile)
    # assert new_role_c.rc.memory == role_c.rc.memory
    # assert new_role_c.rc.env != role_c.rc.env
    assert new_role_c.recovered != role_c.recovered  # here cause previous ut is `!=`
    assert new_role_c.rc.todo != role_c.rc.todo  # serialize exclude `rc.todo`
    assert new_role_c.rc.news != role_c.rc.news  # serialize exclude `rc.news`

    new_company.run_project(idea)
    await new_company.run(n_round=4)


@pytest.mark.asyncio
@pytest.mark.usefixtures("llm_mock")
async def test_team_recover_multi_roles_save():
    idea = "write a snake game"
    stg_path = SERDESER_PATH.joinpath("team")
    shutil.rmtree(stg_path, ignore_errors=True)

    role_a = RoleA()
    role_b = RoleB()

    company = Team()
    company.hire([role_a, role_b])
    company.run_project(idea)
    await company.run(n_round=4)

    logger.info("Team recovered")

    new_company = Team.deserialize(stg_path)
    new_company.run_project(idea)

    assert new_company.env.get_role(role_b.profile).rc.state == 1

    await new_company.run(n_round=4)
