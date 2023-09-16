#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/16 20:03
@Author  : femto Zheng
@File    : test_basic_planner.py
"""
import os

import pytest
from semantic_kernel.core_skills import TextSkill

from metagpt.actions import BossRequirement
from metagpt.roles.sk_agent import SkAgent
from metagpt.schema import Message

# Get the directory of the current file
current_file_directory = os.path.dirname(os.path.abspath(__file__))
# Construct the skills_directory by joining the parent directory and "skillss"
skills_directory = os.path.join(current_file_directory, "..", "skills")
# Normalize the path to ensure it's in the correct format
skills_directory = os.path.normpath(skills_directory)


@pytest.mark.asyncio
async def test_basic_planner():
    task = """
        Tomorrow is Valentine's day. I need to come up with a few date ideas. She speaks French so write it in French.
        Convert the text to uppercase"""
    role = SkAgent()

    # let's give the agent some skills
    role.import_semantic_skill_from_directory(skills_directory, "SummarizeSkill")
    role.import_semantic_skill_from_directory(skills_directory, "WriterSkill")
    role.import_skill(TextSkill(), "TextSkill")
    # using BasicPlanner
    role.recv(Message(content=task, cause_by=BossRequirement))
    await role._think()
    # assuming sk_agent will think he needs WriterSkill.Brainstorm and WriterSkill.Translate
    assert "WriterSkill.Brainstorm" in role.plan.generated_plan.result
    assert "WriterSkill.Translate" in role.plan.generated_plan.result
    # assert "SALUT" in (await role._act()).content #content will be some French
