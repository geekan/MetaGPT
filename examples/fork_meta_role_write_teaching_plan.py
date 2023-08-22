#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/7
@Author  : mashenquan
@File    : fork_meta_role.py
@Desc   : I am attempting to incorporate certain symbol concepts from UML into MetaGPT, enabling it to possess the
            ability to construct flows freely by concatenating symbols. Simultaneously, I am also striving to make
            these symbols configurable and standardized, making the process of building flow structures more
            convenient. This is a fork meta-role demo that implements the functionality of
            `examples/write_teaching_plan.py`.
"""

import asyncio
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
import aiofiles
import fire
import yaml

from metagpt.actions.meta_action import MetaAction
from metagpt.logs import logger
from metagpt.roles.uml_meta_role_factory import UMLMetaRoleFactory
from metagpt.roles.uml_meta_role_options import ProjectConfig
from metagpt.software_company import SoftwareCompany


async def startup(lesson_file: str, investment: float = 3.0, n_round: int = 1, *args, **kwargs):
    """Run a startup. Be a teacher in education industry."""

    demo_lesson = """
    UNIT 1 Making New Friends
    TOPIC 1 Welcome to China!
    Section A

    1a Listen and number the following names.
    Jane Mari Kangkang Michael
    Look, listen and understand. Then practice the conversation.
    Work in groups. Introduce yourself using
    I ’m ... Then practice 1a
    with your own hometown or the following places.

    1b Listen and number the following names
    Jane Michael Maria Kangkang
    1c Work in groups. Introduce yourself using I ’m ... Then practice 1a with your own hometown or the following places.
    China the USA the UK Hong Kong Beijing

    2a Look, listen and understand. Then practice the conversation
    Hello! 
    Hello! 
    Hello! 
    Hello! Are you Maria? 
    No, I’m not. I’m Jane.
    Oh, nice to meet you, Jane
    Nice to meet you, too.
    Hi, Maria!
    Hi, Kangkang!
    Welcome to China!
    Thanks.

    2b Work in groups. Make up a conversation with your own name and the
    following structures.
    A: Hello! / Good morning! / Hi! I’m ... Are you ... ?
    B: ...

    3a Listen, say and trace
    Aa Bb Cc Dd Ee Ff Gg

    3b Listen and number the following letters. Then circle the letters with the same sound as Bb.
    Aa Bb Cc Dd Ee Ff Gg

    3c Match the big letters with the small ones. Then write them on the lines.
    """

    lesson = ""
    if lesson_file and Path(lesson_file).exists():
        async with aiofiles.open(lesson_file, mode="r", encoding="utf-8") as reader:
            lesson = await reader.read()
            logger.info(f"Course content: {lesson}")
    if not lesson:
        logger.info("No course content provided, using the demo course.")
        lesson = demo_lesson

    yaml_filename = kwargs["config"]
    kwargs["lesson"] = lesson

    with open(yaml_filename, "r") as reader:
        configs = yaml.safe_load(reader)

    startup_config = ProjectConfig(**configs)
    company = SoftwareCompany()
    roles = UMLMetaRoleFactory.create_roles(role_configs=startup_config.roles,
                                            options=company.options,
                                            cost_manager=company.cost_manager,
                                            **kwargs)
    company.hire(roles)
    company.invest(startup_config.startup.investment)
    company.start_project(lesson, role=startup_config.startup.role,
                          cause_by=MetaAction.get_action_type(startup_config.startup.requirement))
    await company.run(n_round=startup_config.startup.n_round)


def main(idea: str, investment: float = 3.0, n_round: int = 5, *args, **kwargs):
    """
    We are a software startup comprised of AI. By investing in us, you are empowering a future filled with limitless possibilities.
    :param idea: lesson filename.
    :param investment: As an investor, you have the opportunity to contribute a certain dollar amount to this AI company.
    :param n_round: Reserved.
    :param args: Parameters passed in format: `python your_script.py arg1 arg2 arg3`
    :param kwargs: Parameters passed in format: `python your_script.py --param1=value1 --param2=value2`
    :return:
    """
    asyncio.run(startup(idea, investment, n_round, *args, **kwargs))


if __name__ == '__main__':
    """
    Formats:
    ```
    python write_teaching_plan.py lesson_filename --teaching_language=<the language you are teaching> --language=<your native language>
    ```
    If `lesson_filename` is not available, a demo lesson content will be used.
    """
    fire.Fire(main)
