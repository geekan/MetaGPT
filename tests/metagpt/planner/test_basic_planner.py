#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/16 20:03
@Author  : femto Zheng
@File    : test_basic_planner.py
@Modified By: mashenquan, 2023-11-1. In accordance with Chapter 2.2.1 and 2.2.2 of RFC 116, utilize the new message
        distribution feature for message handling.
"""
import pytest
from semantic_kernel.core_skills import TextSkill

from metagpt.actions import UserRequirement
from metagpt.const import SKILL_DIRECTORY
from metagpt.roles.sk_agent import SkAgent
from metagpt.schema import Message


@pytest.mark.asyncio
async def test_basic_planner():
    task = """
        Tomorrow is Valentine's day. I need to come up with a few date ideas. She speaks French so write it in French.
        Convert the text to uppercase"""
    role = SkAgent()

    # let's give the agent some skills
    role.import_semantic_skill_from_directory(SKILL_DIRECTORY, "SummarizeSkill")
    role.import_semantic_skill_from_directory(SKILL_DIRECTORY, "WriterSkill")
    role.import_skill(TextSkill(), "TextSkill")
    # using BasicPlanner
    role.put_message(Message(content=task, cause_by=UserRequirement))
    await role._observe()
    await role._think()
    # assuming sk_agent will think he needs WriterSkill.Brainstorm and WriterSkill.Translate
    assert "WriterSkill.Brainstorm" in role.plan.generated_plan.result
    assert "WriterSkill.Translate" in role.plan.generated_plan.result
    # assert "SALUT" in (await role._act()).content #content will be some French
