#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/22
@Author  : alexanderwu
@File    : debate_simple.py
"""
import asyncio

from metagpt.actions import Action, UserRequirement
from metagpt.environment import Environment
from metagpt.roles import Role
from metagpt.team import Team

action1 = Action(name="BidenSay", instruction="发表政见，充满激情的反驳特朗普最新消息，尽最大努力获得选票")
action2 = Action(name="TrumpSay", instruction="发表政见，充满激情的反驳拜登最新消息，尽最大努力获得选票，MAGA！")
biden = Role(name="拜登", profile="民主党候选人", goal="大选获胜", actions=[action1], watch=[action2, UserRequirement])
trump = Role(name="特朗普", profile="共和党候选人", goal="大选获胜", actions=[action2], watch=[action1])
env = Environment(desc="US election live broadcast")
team = Team(investment=10.0, env=env, roles=[biden, trump])

asyncio.run(team.run(idea="主题：气候变化，用中文辩论", n_round=5))
