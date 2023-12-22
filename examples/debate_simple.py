#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/22
@Author  : alexanderwu
@File    : debate_simple.py
"""
import asyncio

from metagpt.actions import Action, UserRequirement
from metagpt.roles import Role
from metagpt.team import Team

action1 = Action(name="BidenSay", instruction="Use diverse words to attack your opponent, strong and emotional.")
action2 = Action(name="TrumpSay", instruction="Use diverse words to attack your opponent, strong and emotional.")
biden = Role(name="Biden", profile="democrat", goal="win election", actions=[action1], watch=[action2, UserRequirement])
trump = Role(name="Trump", profile="republican", goal="win election", actions=[action2], watch=[action1])
team = Team(investment=10.0, env_desc="US election live broadcast", roles=[biden, trump])

asyncio.run(team.run(idea="Topic: climate change", n_round=5))
