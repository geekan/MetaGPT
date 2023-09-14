#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/13 12:36
@Author  : femto Zheng
@File    : sk_agent.py
"""
import asyncio
import os

from semantic_kernel.core_skills import FileIOSkill, MathSkill, TextSkill, TimeSkill
from semantic_kernel.planning import SequentialPlanner

# from semantic_kernel.planning import SequentialPlanner
from semantic_kernel.planning.action_planner.action_planner import ActionPlanner

from metagpt.actions import BossRequirement
from metagpt.roles.sk_agent import SkAgent
from metagpt.schema import Message
from metagpt.tools.search_engine import SkSearchEngine

# Get the directory of the current file
current_file_directory = os.path.dirname(os.path.abspath(__file__))
# Construct the skills_directory by joining the parent directory and "skillss"
skills_directory = os.path.join(current_file_directory, "..", "metagpt", "skills")
# Normalize the path to ensure it's in the correct format
skills_directory = os.path.normpath(skills_directory)


async def main():
    # await basic_planner_example()
    # await action_planner_example()

    # await sequential_planner_example()
    await basic_planner_web_search_example()


async def basic_planner_example():
    task = """
    Tomorrow is Valentine's day. I need to come up with a few date ideas. She speaks French so write it in French.
    Convert the text to uppercase"""
    role = SkAgent()

    # let's give the agent some skills
    role.import_semantic_skill_from_directory(skills_directory, "SummarizeSkill")
    role.import_semantic_skill_from_directory(skills_directory, "WriterSkill")
    role.import_skill(TextSkill(), "TextSkill")
    # using BasicPlanner
    await role.run(Message(content=task, cause_by=BossRequirement))


async def sequential_planner_example():
    task = """
    Tomorrow is Valentine's day. I need to come up with a few date ideas. She speaks French so write it in French.
    Convert the text to uppercase"""
    role = SkAgent(planner_cls=SequentialPlanner)

    # let's give the agent some skills
    role.import_semantic_skill_from_directory(skills_directory, "SummarizeSkill")
    role.import_semantic_skill_from_directory(skills_directory, "WriterSkill")
    role.import_skill(TextSkill(), "TextSkill")
    # using BasicPlanner
    await role.run(Message(content=task, cause_by=BossRequirement))


async def basic_planner_web_search_example():
    task = """
    Question: Who made the 1989 comic book, the film version of which Jon Raymond Polito appeared in?"""
    role = SkAgent()

    role.import_skill(SkSearchEngine(), "WebSearchSkill")
    # role.import_semantic_skill_from_directory(skills_directory, "QASkill")

    await role.run(Message(content=task, cause_by=BossRequirement))


async def action_planner_example():
    role = SkAgent(planner_cls=ActionPlanner)
    # let's give the agent 4 skills
    role.import_skill(MathSkill(), "math")
    role.import_skill(FileIOSkill(), "fileIO")
    role.import_skill(TimeSkill(), "time")
    role.import_skill(TextSkill(), "text")
    task = "What is the sum of 110 and 990?"
    await role.run(Message(content=task, cause_by=BossRequirement))  # it will choose mathskill.Add


if __name__ == "__main__":
    asyncio.run(main())
