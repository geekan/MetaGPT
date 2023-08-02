#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio

import fire

from metagpt.roles import Architect, Engineer, ProductManager, ProjectManager
from metagpt.software_company import SoftwareCompany


async def startup(idea: str, investment: float = 3.0, n_round: int = 5, code_review: bool = False):
    """Run a startup. Be a boss."""
    company = SoftwareCompany()
    company.hire([ProductManager(),
                  Architect(),
                  ProjectManager(),
                  Engineer(n_borg=5, use_code_review=code_review)])
    company.invest(investment)
    company.start_project(idea)
    await company.run(n_round=n_round)


def main(idea: str, investment: float = 3.0, n_round: int = 5, code_review: bool = False):
    """
    We are a software startup comprised of AI. By investing in us, you are empowering a future filled with limitless possibilities.
    :param idea: Your innovative idea, such as "Creating a snake game."
    :param investment: As an investor, you have the opportunity to contribute a certain dollar amount to this AI company.
    :param n_round:
    :param code_review: Whether to use code review.
    :return:
    """
    asyncio.run(startup(idea, investment, n_round, code_review))


if __name__ == '__main__':
    fire.Fire(main)
    