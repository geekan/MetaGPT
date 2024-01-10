#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of team

from metagpt.roles.project_manager import ProjectManager
from metagpt.team import Team


def test_team():
    company = Team()
    company.hire([ProjectManager()])

    assert len(company.env.roles) == 1
