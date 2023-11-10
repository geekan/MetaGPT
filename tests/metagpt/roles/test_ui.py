# -*- coding: utf-8 -*-
# @Date    : 2023/7/22 02:40
# @Author  : stellahong (stellahong@fuzhi.ai)
#
from metagpt.team import Team
from metagpt.roles import ProductManager

from tests.metagpt.roles.ui_role import UI


def test_add_ui():
    ui = UI()
    assert ui.profile == "UI Design"


async def test_ui_role(idea: str, investment: float = 3.0, n_round: int = 5):
    """Run a startup. Be a boss."""
    company = Team()
    company.hire([ProductManager(), UI()])
    company.invest(investment)
    company.start_project(idea)
    await company.run(n_round=n_round)
