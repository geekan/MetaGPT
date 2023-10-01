#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : StanfordTown to works like SoftwareCompany

from pydantic import Field

from metagpt.software_company import SoftwareCompany
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.logs import logger

from maze_environment import MazeEnvironment
from actions.user_requirement import UserRequirement


class StanfordTown(SoftwareCompany):

    environment: MazeEnvironment = Field(default_factory=MazeEnvironment)

    def wakeup_roles(self, roles: list[Role]):
        logger.warning(f"The Town add {len(roles)} roles, and start to operate.")
        self.environment.add_roles(roles)

    def start_project(self, idea):
        self.environment.publish_message(
            Message(role="User", content=idea, cause_by=UserRequirement)
        )
