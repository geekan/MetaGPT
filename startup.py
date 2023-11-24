#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import os
import platform

import fire

from metagpt.roles import (
    Architect,
    Engineer,
    ProductManager,
    ProjectManager,
    QaEngineer,
)
from metagpt.schema import Message
from metagpt.team import Team
from metagpt.utils.special_tokens import MSG_SEP


async def startup(
    idea: str,
    difference_description: str = "",
    project_path: str = "",
    investment: float = 3.0,
    n_round: int = 5,
    code_review: bool = False,
    run_tests: bool = False,
    implement: bool = True,
    increment: bool = False,
    bug_fix: bool = False,
):
    """Run a startup. Be a boss."""
    company = Team()

    if increment or bug_fix:
        # 读取文件
        prd_path = os.path.join(project_path, 'docs/prd.md')
        design_path = os.path.join(project_path, 'docs/system_design.md')
        api_spec_and_tasks_path = os.path.join(project_path, 'docs/api_spec_and_tasks.md')
        code_path = os.path.join(project_path, os.path.basename(project_path))

        with open(prd_path, 'r', encoding='utf-8') as f:
            legacy_prd = f.read()

        with open(design_path, 'r', encoding='utf-8') as f:
            legacy_design = f.read()

        with open(api_spec_and_tasks_path, 'r', encoding='utf-8') as f:
            legacy_api_spec_and_tasks = f.read()

        # 遍历文件夹，获取所有代码文件
        legacy_code = ''
        for root, dirs, files in os.walk(code_path):
            filenames = [filename for filename in files if filename.endswith('.py')]
            legacy_code += f'There are {len(files)} scripts in the current folder: {", ".join(filenames)}\n---\n'
            for file in files:
                if file.endswith('.py'):
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        legacy_code += f.read() + '\n---\n'

        if bug_fix:
            boss_msg = Message(
                content=f"Boss's requirement\n:{idea}\n---\nBoss's difference description:{difference_description}\n---\n",
                sent_from="Boss",
            )
            product_manager_msg = Message(
                content=f"Product Manager's prd legacy:\n{legacy_prd}\n---\n",
                sent_from="ProductManager"
            )
            architect_msg = Message(
                content=f"Architect's design legacy:\n{legacy_design}\n---\n",
                sent_from="Architect"
            )
            project_manager_msg = Message(
                content=f"Project Manager's api spec and tasks legacy:\n{legacy_api_spec_and_tasks}\n---\n",
                sent_from="ProjectManager"
            )
            engineer_msg = Message(
                content=f"Engineer's code legacy:\n{legacy_code}\n---\n",
                sent_from="Engineer"
            )
            bug_msgs = [boss_msg, product_manager_msg, architect_msg, project_manager_msg, engineer_msg]
        else:
            company.hire(
                [ProductManager(difference_description=difference_description, legacy=legacy_prd, increment=increment),
                 Architect(legacy=legacy_design, increment=increment),
                 ProjectManager(legacy=legacy_api_spec_and_tasks, increment=increment)])
    else:
        company.hire([ProductManager(), Architect(), ProjectManager()])

    # if implement or code_review
    if bug_fix:
        company.hire([Engineer(n_borg=5, bug_msgs=bug_msgs, bug_fix=bug_fix)])
    elif implement or code_review:
        # developing features: implement the idea
        company.hire([Engineer(n_borg=5, use_code_review=code_review)])
    elif (implement or code_review) and increment:
        company.hire([Engineer(n_borg=5, use_code_review=code_review, legacy=legacy_code, increment=increment)])

    if run_tests or bug_fix:
        # developing features: run tests on the spot and identify bugs
        # (bug fixing capability comes soon!)
        company.hire([QaEngineer()])

    company.invest(investment)
    company.start_project(idea)
    await company.run(n_round=n_round)


def main(
    idea: str,
    difference_description: str = "",
    project_path: str = "",
    investment: float = 3.0,
    n_round: int = 5,
    code_review: bool = True,
    run_tests: bool = False,
    implement: bool = True,
    increment: bool = False,
    bug_fix: bool = False,
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

    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(
        startup(idea, difference_description, project_path, investment, n_round, code_review, run_tests, implement, increment, bug_fix))


if __name__ == "__main__":
    fire.Fire(main)
