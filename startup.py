#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Optional
import asyncio
import fire
from pathlib import Path

from metagpt.roles import (
    Architect,
    Engineer,
    ProductManager,
    ProjectManager,
    QaEngineer,
)
from metagpt.team import Team


async def startup(
    idea: str,
    investment: float = 3.0,
    n_round: int = 5,
    code_review: bool = False,
    run_tests: bool = False,
    implement: bool = True,
    recover_path: Optional[str] = None,
):
    """Run a startup. Be a boss."""
    if not recover_path:
        company = Team()
        company.hire(
            [
                ProductManager(),
                Architect(),
                ProjectManager(),
            ]
        )

        # if implement or code_review
        if implement or code_review:
            # developing features: implement the idea
            company.hire([Engineer(n_borg=5, use_code_review=code_review)])

        if run_tests:
            # developing features: run tests on the spot and identify bugs
            # (bug fixing capability comes soon!)
            company.hire([QaEngineer()])
    else:
        # # stg_path = SERDESER_PATH.joinpath("team")
        stg_path = Path(recover_path)
        if not stg_path.exists() or not str(stg_path).endswith("team"):
            raise FileNotFoundError(f"{recover_path} not exists or not endswith `team`")

        company = Team.recover(stg_path=stg_path)
        idea = company.idea  # use original idea

    company.invest(investment)
    company.start_project(idea)
    await company.run(n_round=n_round)


def main(
    idea: str,
    investment: float = 3.0,
    n_round: int = 5,
    code_review: bool = True,
    run_tests: bool = False,
    implement: bool = True,
    recover_path: str = None,
):
    """
    We are a software startup comprised of AI. By investing in us,
    you are empowering a future filled with limitless possibilities.
    :param idea: Your innovative idea, such as "Creating a snake game."
    :param investment: As an investor, you have the opportunity to contribute
    a certain dollar amount to this AI company.
    :param n_round:
    :param code_review: Whether to use code review.
    :param recover_path: recover the project from existing serialized storage
    :return:
    """
    asyncio.run(startup(idea, investment, n_round, code_review, run_tests, implement, recover_path))


if __name__ == "__main__":
    fire.Fire(main)
