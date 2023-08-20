#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : architect.py
@Modified By: mashenquan, 2023/8/20. Remove global configuration `CONFIG`, enable configuration support for business isolation;
            Change cost control from global to company level.
"""

from metagpt.actions import WriteDesign, WritePRD
from metagpt.roles import Role


class Architect(Role):
    """Architect: Listen to PRD, responsible for designing API, designing code files"""
    def __init__(self, options, cost_manager, name="Bob", profile="Architect", goal="Design a concise, usable, complete python system",
                 constraints="Try to specify good open source tools as much as possible"):
        super().__init__(name=name, profile=profile, goal=goal, constraints=constraints, options=options, cost_manager=cost_manager)
        self._init_actions([WriteDesign])
        self._watch({WritePRD})
