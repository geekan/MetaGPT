#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import os

import fire

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
    difference_description: str = "",
    path: str = "",
    investment: float = 3.0,
    n_round: int = 5,
    code_review: bool = False,
    run_tests: bool = False,
    implement: bool = True,
    increment: bool = False,
):
    """Run a startup. Be a boss."""
    company = Team()

    if increment:
        # 读取文件
        prd_path = os.path.join(path, 'docs/prd.md')
        design_path = os.path.join(path, 'docs/system_design.md')
        api_spec_path = os.path.join(path, 'docs/api_spec_and_tasks.md')
        code_path = os.path.join(path, os.path.basename(path))

        with open(prd_path, 'r', encoding='utf-8') as f:
            legacy_prd = f.read()

        with open(design_path, 'r', encoding='utf-8') as f:
            legacy_design = f.read()

        with open(api_spec_path, 'r', encoding='utf-8') as f:
            legacy_api_spec = f.read()

        # 遍历文件夹，获取所有代码文件
        legacy_code = ''
        for root, dirs, files in os.walk(code_path):
            filenames = [filename for filename in files if filename.endswith('.py')]
            legacy_code += f'There are {len(files)} scripts in the current folder: {", ".join(filenames)}\n\n'
            for file in files:
                if file.endswith('.py'):
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        legacy_code += f.read() + '\n\n'

        company.hire(
            [ProductManager(difference_description=difference_description, legacy=legacy_prd, increment=increment),
             Architect(legacy=legacy_design, increment=increment),
             ProjectManager(legacy=legacy_api_spec, increment=increment)])
    else:
        company.hire([ProductManager(), Architect(), ProjectManager()])

    # if implement or code_review
    if (implement or code_review) and not increment:
        # developing features: implement the idea
        company.hire([Engineer(n_borg=5, use_code_review=code_review)])
    elif (implement or code_review) and increment:
        company.hire([Engineer(n_borg=5, use_code_review=code_review, legacy=legacy_code, increment=increment)])

    if run_tests:
        # developing features: run tests on the spot and identify bugs
        # (bug fixing capability comes soon!)
        company.hire([QaEngineer()])

    company.invest(investment)
    company.start_project(idea)
    await company.run(n_round=n_round)


def main(
    idea: str,
    difference_description: str = "",
    path: str = "",
    investment: float = 3.0,
    n_round: int = 5,
    code_review: bool = True,
    run_tests: bool = False,
    implement: bool = True,
    increment: bool = False,
):
    """
    We are a software startup comprised of AI. By investing in us,
    you are empowering a future filled with limitless possibilities.
    :param idea: Your innovative idea, such as "Creating a snake game."
    :param investment: As an investor, you have the opportunity to contribute
    a certain dollar amount to this AI company.
    :param n_round:
    :param code_review: Whether to use code review.
    :return:
    """
    asyncio.run(
        startup(idea, difference_description, path, investment, n_round, code_review, run_tests, implement, increment))


if __name__ == "__main__":
    fire.Fire(main)
