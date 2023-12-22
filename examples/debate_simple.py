#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/22
@Author  : alexanderwu
@File    : debate_simple.py
"""
import asyncio

from metagpt.actions import Action
from metagpt.environment import Environment
from metagpt.roles import Role
from metagpt.team import Team

action1 = Action(name="BidenSay", instruction="Passionately refute Trump's latest news, and strive to gain votes")
action2 = Action(name="TrumpSay", instruction="Passionately refute Biden's latest news, and strive to gain votes")
biden = Role(name="Biden", profile="Democratic candidate", goal="Win the election", actions=[action1], watch=[action2])
trump = Role(name="Trump", profile="Republican candidate", goal="Win the election", actions=[action2], watch=[action1])
env = Environment(desc="US election live broadcast")
team = Team(investment=10.0, env=env, roles=[biden, trump])

asyncio.run(team.run(idea="Topic: Climate Change", send_to="Biden", n_round=5))
