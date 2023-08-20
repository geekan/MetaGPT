#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Modified By: mashenquan, 2023/8/20. Remove global configuration `CONFIG`, enable configuration support for business isolation;
            Change cost control from global to company level.
"""

import asyncio

import fire

from metagpt.roles import Architect, Engineer, ProductManager, ProjectManager, QaEngineer
from metagpt.software_company import SoftwareCompany


async def startup(idea: str, investment: float = 3.0, n_round: int = 5,
                  code_review: bool = False, run_tests: bool = False):
    """Run a startup. Be a boss."""

    company = SoftwareCompany()
    company.hire([ProductManager(options=company.options, cost_manager=company.cost_manager),
                  Architect(options=company.options, cost_manager=company.cost_manager),
                  ProjectManager(options=company.options, cost_manager=company.cost_manager),
                  Engineer(n_borg=5, use_code_review=code_review, options=company.options, cost_manager=company.cost_manager)])
    if run_tests:
        # developing features: run tests on the spot and identify bugs (bug fixing capability comes soon!)
        company.hire([QaEngineer(options=company.options, cost_manager=company.cost_manager)])
    company.invest(investment)
    company.start_project(idea)
    await company.run(n_round=n_round)


def main(idea: str, investment: float = 3.0, n_round: int = 5, code_review: bool = False, run_tests: bool = False):
    """
    We are a software startup comprised of AI. By investing in us, you are empowering a future filled with limitless possibilities.
    :param idea: Your innovative idea, such as "Creating a snake game."
    :param investment: As an investor, you have the opportunity to contribute a certain dollar amount to this AI company.
    :param n_round:
    :param code_review: Whether to use code review.
    :return:
    """
    asyncio.run(startup(idea, investment, n_round, code_review, run_tests))


if __name__ == '__main__':
    fire.Fire(main)
