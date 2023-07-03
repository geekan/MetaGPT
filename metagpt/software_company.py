#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 00:30
@Author  : alexanderwu
@File    : software_company.py
"""
import asyncio

import fire

from metagpt.config import Config
from metagpt.actions import BossRequirement
from metagpt.logs import logger
from metagpt.environment import Environment
from metagpt.roles import ProductManager, Architect, Engineer, QaEngineer, ProjectManager, Role
from metagpt.manager import Manager
from metagpt.schema import Message
from metagpt.utils.common import NoMoneyException


class SoftwareCompany:
    """
    Software Company: Possesses a team, SOP (Standard Operating Procedures), and a platform for instant messaging,
    dedicated to writing executable code.
    """
    def __init__(self):
        self.environment = Environment()
        self.config = Config()
        self.investment = 0
        self.idea = ""

    def hire(self, roles: list[Role]):
        """Hire roles to cooperate"""
        self.environment.add_roles(roles)

    def invest(self, investment: float):
        """Invest company. raise NoMoneyException when exceed max_budget."""
        self.investment = investment
        self.config.max_budget = investment

    def _check_balance(self):
        if self.config.total_cost > self.config.max_budget:
            raise NoMoneyException(self.config.total_cost, f'Insufficient funds: {self.config.max_budget}')

    def start_project(self, idea):
        """Start a project from publish boss requirement."""
        self.idea = idea
        self.environment.publish_message(Message(role="BOSS", content=idea, cause_by=BossRequirement))

    async def run(self, n_round=3):
        """Run company until target round"""
        while not self.environment.message_queue.empty():
            self._check_balance()
            n_round -= 1
            logger.debug(f"{n_round=}")
            if n_round == 0:
                return
            await self.environment.run()
        return self.environment.history
