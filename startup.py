#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Modified By: mashenquan, 2023-07-27, +industry concept
"""

import asyncio
from pathlib import Path
import aiofiles
import fire
from metagpt.logs import logger
from metagpt.actions.write_teaching_plan import TeachingPlanRequirement
from metagpt.roles import Architect, Engineer, ProductManager, ProjectManager
from metagpt.roles.teacher import Teacher
from metagpt.software_company import SoftwareCompany


async def software_startup(investment: float = 3.0, n_round: int = 5, code_review: bool = False, *args, **kwargs):
    """Run a startup. Be a boss in software industry."""
    idea = kwargs['idea']  # Your innovative idea, such as "Creating a snake game."
    company = SoftwareCompany()
    company.hire([ProductManager(),
                  Architect(),
                  ProjectManager(),
                  Engineer(n_borg=5, use_code_review=code_review)])
    company.invest(investment)
    company.start_project(idea)
    await company.run(n_round=n_round)


async def education_startup(investment: float = 3.0, n_round: int = 5, code_review: bool = False, *args, **kwargs):
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

    3b Listen and number the following letters. Then circle the letters withthe same sound as Bb.
    Aa Bb Cc Dd Ee Ff Gg

    3c Match the big letters with the small ones. Then write them on the lines.
    """

    lesson = ""
    lesson_file = kwargs.get('lesson_file')
    if lesson_file is not None and Path(lesson_file).exists():
        async with aiofiles.open(lesson_file, mode="r", encoding="utf-8") as reader:
            lesson = await reader.read()
            logger.info(f"Course content: {lesson}")
    if not lesson:
        logger.info("No course content provided, using the demo course.")
        lesson = demo_lesson

    company = SoftwareCompany()
    company.hire([Teacher(*args, **kwargs)])
    company.invest(investment)
    company.start_project(lesson, role="Teacher", cause_by=TeachingPlanRequirement)
    await company.run(n_round=1)


def main(investment: float = 3.0, n_round: int = 5, code_review: bool = False, *args, **kwargs):
    """
    We are a software startup comprised of AI. By investing in us, you are empowering a future filled with limitless possibilities.
    :param investment: As an investor, you have the opportunity to contribute a certain dollar amount to this AI company.
    :param n_round:
    :param code_review: Whether to use code review.
    :param args: Parameters passed in format: `python your_script.py arg1 arg2 arg3`
    :param kwargs: Parameters passed in format: `python your_script.py a--param1=value1 --param2=value2`
    :return:
    """
    industry = kwargs.get("industry", "software")
    industries = {
        "software": software_startup,
        "education": education_startup,
    }
    startup = industries.get(industry)
    if startup is None:
        print(f"Available industries:{list(industries.keys())}")
        return
    asyncio.run(startup(investment, n_round, code_review, *args, **kwargs))


if __name__ == '__main__':
    fire.Fire(main)
