#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/22 00:15
@Author  : alexanderwu
@File    : debate_simple.py
"""
import asyncio

from metagpt.actions import Action
from metagpt.roles import Role
from metagpt.team import Team

action = Action(name="Debate", instruction="respond to opponent's latest argument, strong and emotional.")
biden = Role(name="Biden", profile="Democrat", actions=[action], watch=[action])
trump = Role(name="Trump", profile="Republican", actions=[action], watch=[action])
team = Team(investment=10.0, env_desc="US election live broadcast", roles=[biden, trump])

asyncio.run(team.run(idea="Topic: climate change", n_round=5))
