#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 00:30
@Author  : alexanderwu
@File    : software_company.py
"""
from pydantic import BaseModel, Field

from metagpt.actions import BossRequirement, Feedback
from metagpt.config import CONFIG
from metagpt.environment import Environment
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.utils.common import NoMoneyException

def print_with_color(text, color="red"):

    color_codes = {
        'reset': '\033[0m',
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
    }
    print(f"{color_codes[color]}  {text} {color_codes['reset']}")

class SoftwareCompany(BaseModel):
    """
    Software Company: Possesses a team, SOP (Standard Operating Procedures), and a platform for instant messaging,
    dedicated to writing executable code.
    """
    environment: Environment = Field(default_factory=Environment)
    investment: float = Field(default=10.0)
    idea: str = Field(default="")

    class Config:
        arbitrary_types_allowed = True

    def hire(self, roles: list[Role]):
        """Hire roles to cooperate"""
        self.environment.add_roles(roles)

    def invest(self, investment: float):
        """Invest company. raise NoMoneyException when exceed max_budget."""
        self.investment = investment
        CONFIG.max_budget = investment
        logger.info(f'Investment: ${investment}.')

    def improvement(self, initial=False, roles=None):
        handover_file = CONFIG.handover_file
        if initial:
            import os
            import json
            os.makedirs(os.path.dirname(handover_file), exist_ok=True)
            if not os.path.exists(handover_file):
                with open(handover_file, "w") as file:
                    json.dump({}, file)
        else:
            msgs = self.environment.memory.get_by_action(Feedback)
            print_with_color("===============\n\n\n\n\n")
            print_with_color(msgs)
            if isinstance(msgs, list):
                for msg in msgs:
                    print_with_color(msg.content)
            print_with_color(roles)
            print_with_color("===============\n\n\n\n\n")

            


    def _check_balance(self):
        if CONFIG.total_cost > CONFIG.max_budget:
            raise NoMoneyException(CONFIG.total_cost, f'Insufficient funds: {CONFIG.max_budget}')

    def start_project(self, idea):
        """Start a project from publishing boss requirement."""
        self.idea = idea
        self.environment.publish_message(Message(role="BOSS", content=idea, cause_by=BossRequirement))

    def _save(self):
        logger.info(self.json())

    async def run(self, n_round=3):
        """Run company until target round or no money"""
        while n_round > 0:
            # self._save()
            n_round -= 1
            logger.debug(f"{n_round=}")
            self._check_balance()
            await self.environment.run()
        return self.environment.history
    