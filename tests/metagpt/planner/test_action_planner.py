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
from semantic_kernel.core_skills import FileIOSkill, MathSkill, TextSkill, TimeSkill
from semantic_kernel.planning.action_planner.action_planner import ActionPlanner

from metagpt.actions import UserRequirement
from metagpt.roles.sk_agent import SkAgent
from metagpt.schema import Message


@pytest.mark.asyncio
async def test_action_planner():
    role = SkAgent(planner_cls=ActionPlanner)
    # let's give the agent 4 skills
    role.import_skill(MathSkill(), "math")
    role.import_skill(FileIOSkill(), "fileIO")
    role.import_skill(TimeSkill(), "time")
    role.import_skill(TextSkill(), "text")
    task = "What is the sum of 110 and 990?"

    role.put_message(Message(content=task, cause_by=UserRequirement))
    await role._observe()
    await role._think()  # it will choose mathskill.Add
    assert "1100" == (await role._act()).content
