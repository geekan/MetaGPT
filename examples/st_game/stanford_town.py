#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : StanfordTown to works like SoftwareCompany

from pydantic import Field

from metagpt.software_company import SoftwareCompany
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.logs import logger

from examples.st_game.maze_environment import MazeEnvironment
from examples.st_game.actions.user_requirement import UserRequirement


class StanfordTown(SoftwareCompany):

    environment: MazeEnvironment = Field(default_factory=MazeEnvironment)

    def wakeup_roles(self, roles: list[Role]):
        logger.warning(f"The Town add {len(roles)} roles, and start to operate.")
        self.environment.add_roles(roles)

    def start_project(self, idea):
        self.environment.publish_message(
            Message(role="User", content=idea, cause_by=UserRequirement)
        )

    async def run(self, n_round: int = 3):
        """Run company until target round or no money"""
        while n_round > 0:
            # self._save()
            n_round -= 1
            logger.debug(f"{n_round=}")
            self._check_balance()
            await self.environment.run()

        # save simulation result including environment and roles after all rounds
        roles = self.environment.get_roles()
        for profile, role in roles.items():
            role.save_into()

        return self.environment.history
