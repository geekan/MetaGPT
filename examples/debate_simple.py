#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/22
@Author  : alexanderwu
@File    : debate_simple.py
"""
import asyncio

from metagpt.actions import Action
from metagpt.config2 import Config
from metagpt.environment import Environment
from metagpt.roles import Role
from metagpt.team import Team

gpt35 = Config.default()
gpt35.llm.model = "gpt-3.5-turbo-1106"
gpt4 = Config.default()
gpt4.llm.model = "gpt-4-1106-preview"
action1 = Action(config=gpt4, name="AlexSay", instruction="Express your opinion with emotion and don't repeat it")
action2 = Action(config=gpt35, name="BobSay", instruction="Express your opinion with emotion and don't repeat it")
alex = Role(name="Alex", profile="Democratic candidate", goal="Win the election", actions=[action1], watch=[action2])
bob = Role(name="Bob", profile="Republican candidate", goal="Win the election", actions=[action2], watch=[action1])
env = Environment(desc="US election live broadcast")
team = Team(investment=10.0, env=env, roles=[alex, bob])

asyncio.run(team.run(idea="Topic: climate change. Under 80 words per message.", send_to="Alex", n_round=5))
