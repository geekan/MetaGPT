#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 00:30
@Author  : alexanderwu
@File    : software_company.py
@Modified By: mashenquan, 2023/8/20. Remove global configuration `CONFIG`, enable configuration support for business isolation;
            Change cost control from global to company level.
"""
from typing import Dict

from pydantic import BaseModel, Field

from metagpt.actions import BossRequirement
from metagpt.environment import Environment
from metagpt.logs import logger
from metagpt.provider.openai_api import CostManager
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.utils.common import NoMoneyException
from metagpt.config import Config


class SoftwareCompany(BaseModel):
    """
    Software Company: Possesses a team, SOP (Standard Operating Procedures), and a platform for instant messaging,
    dedicated to writing executable code.
    """
    environment: Environment = Field(default_factory=Environment)
    investment: float = Field(default=10.0)
    idea: str = Field(default="")
    options: Dict = Field(default=Config().runtime_options)
    cost_manager: CostManager = Field(default=CostManager(**Config().runtime_options))

    class Config:
        arbitrary_types_allowed = True

    def hire(self, roles: list[Role]):
        """Hire roles to cooperate"""
        self.environment.add_roles(roles)

    def invest(self, investment: float):
        """Invest company. raise NoMoneyException when exceed max_budget."""
        self.investment = investment
        self.options["max_budget"] = investment
        logger.info(f'Investment: ${investment}.')

    def _check_balance(self):
        if self.total_cost > self.max_budget:
            raise NoMoneyException(self.total_cost, f'Insufficient funds: {self.max_budget}')

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

    @property
    def max_budget(self):
        return self.options.get("max_budget", 0)

    @property
    def total_cost(self):
        return self.options.get("total_cost", 0)


