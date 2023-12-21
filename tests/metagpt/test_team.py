#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : unittest of team

from metagpt.team import Team
from metagpt.roles.project_manager import ProjectManager


def test_team():
    company = Team()
    company.hire([ProjectManager()])

    assert len(company.environment.roles) == 1
