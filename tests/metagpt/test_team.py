#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of team

from pathlib import Path
import shutil

from metagpt.team import Team

from tests.metagpt.roles.test_role import RoleA

serdes_path = Path(__file__).absolute().parent.joinpath("../data/serdes_storage")


def test_team_serdes():
    company = Team()
    company.hire([RoleA()])

    stg_path = serdes_path.joinpath("team")
    shutil.rmtree(stg_path, ignore_errors=True)

    company.serialize(stg_path=stg_path)

    new_company = Team()
    new_company.deserialize(stg_path)

    assert len(new_company.environment.roles) == 1
