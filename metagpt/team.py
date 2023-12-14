#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 00:30
@Author  : alexanderwu
@File    : software_company.py
@Modified By: mashenquan, 2023/11/27. Add an archiving operation after completing the project, as specified in
        Section 2.2.3.3 of RFC 135.
"""
from pydantic import BaseModel, Field

from metagpt.actions import UserRequirement
from metagpt.config import CONFIG
from metagpt.const import MESSAGE_ROUTE_TO_ALL
from metagpt.environment import Environment
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.utils.common import NoMoneyException


class Team(BaseModel):
    """
    Team: Possesses one or more roles (agents), SOP (Standard Operating Procedures), and a platform for instant messaging,
    dedicated to perform any multi-agent activity, such as collaboratively writing executable code.
    """

    env: Environment = Field(default_factory=Environment)
    investment: float = Field(default=10.0)
    idea: str = Field(default="")

    class Config:
        arbitrary_types_allowed = True

    def hire(self, roles: list[Role]):
        """Hire roles to cooperate"""
        self.env.add_roles(roles)

    def invest(self, investment: float):
        """Invest company. raise NoMoneyException when exceed max_budget."""
        self.investment = investment
        CONFIG.max_budget = investment
        logger.info(f"Investment: ${investment}.")

    @staticmethod
    def _check_balance():
        if CONFIG.cost_manager.total_cost > CONFIG.cost_manager.max_budget:
            raise NoMoneyException(CONFIG.cost_manager.total_cost,
                                   f'Insufficient funds: {CONFIG.cost_manager.max_budget}')

    def run_project(self, idea, send_to: str = ""):
        """Start a project from publishing user requirement."""
        self.idea = idea

        # Human requirement.
        self.env.publish_message(
            Message(role="Human", content=idea, cause_by=UserRequirement, send_to=send_to or MESSAGE_ROUTE_TO_ALL),
            peekable=False,
        )

    def _save(self):
        logger.info(self.json(ensure_ascii=False))

    async def run(self, n_round=3, auto_archive=True):
        """Run company until target round or no money"""
        while n_round > 0:
            # self._save()
            n_round -= 1
            logger.debug(f"{n_round=}")
            self._check_balance()
            await self.env.run()
        if auto_archive and CONFIG.git_repo:
            CONFIG.git_repo.archive()
        return self.env.history
