# -*- coding: utf-8 -*-
# @Date    : 11/27/2023 10:07 AM
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :

import shutil

import pytest

from metagpt.const import SERDESER_PATH
from metagpt.roles import ProjectManager, ProductManager, Architect
from metagpt.team import Team
from tests.metagpt.serialize_deserialize.test_serdeser_base import RoleA, RoleB, RoleC, serdeser_path, ActionOK


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
    ser_company = company.dict()
    new_company = Team(**ser_company)

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

    ser_data = company.dict()
    new_company = Team(**ser_data)

    new_role_c = new_company.env.get_role(role_c.profile)
    # assert new_role_c._rc.memory == role_c._rc.memory  # TODO
    assert new_role_c._rc.env != role_c._rc.env  # TODO
    assert type(list(new_company.env.roles.values())[0]._actions[0]) == ActionOK

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

    new_company = Team.recover(stg_path)
    new_role_c = new_company.env.get_role(role_c.profile)
    # assert new_role_c._rc.memory == role_c._rc.memory
    assert new_role_c._rc.env != role_c._rc.env
    assert new_role_c.recovered != role_c.recovered  # here cause previous ut is `!=`
    assert new_role_c._rc.todo != role_c._rc.todo  # serialize exclude `_rc.todo`
    assert new_role_c._rc.news != role_c._rc.news  # serialize exclude `_rc.news`

    new_company.run_project(idea)
    await new_company.run(n_round=4)


@pytest.mark.asyncio
async def test_team_recover_multi_roles_save():
    idea = "write a snake game"
    stg_path = SERDESER_PATH.joinpath("team")
    shutil.rmtree(stg_path, ignore_errors=True)

    company = Team()
    company.hire([RoleA(), RoleB()])
    company.run_project(idea)
    await company.run(n_round=4)

    new_company = Team.recover(stg_path)
    new_company.run_project(idea)
    await new_company.run(n_round=4)
