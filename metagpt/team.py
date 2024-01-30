#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/5/12 00:30
# @Author  : alexanderwu
# @File    : team.py
# @Modified By: mashenquan, 2023/11/27. Add an archiving operation after completing the project, as specified in
#         Section 2.2.3.3 of RFC 135.

import warnings
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from metagpt.actions import UserRequirement
from metagpt.const import MESSAGE_ROUTE_TO_ALL, SERDESER_PATH
from metagpt.context import Context
from metagpt.environment import Environment
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.utils.common import (
    NoMoneyException,
    read_json_file,
    serialize_decorator,
    write_json_file,
)


class Team(BaseModel):
    """Team: Possesses one or more roles (agents), SOP (Standard Operating Procedures), and an environment for instant messaging,
    dedicated to any multi-agent activity, such as collaboratively writing executable code.

    Args:
        context: The context in which the team operates.
        **data: Arbitrary keyword arguments.

    Attributes:
        model_config: Configuration dictionary allowing arbitrary types.
        env: Optional environment for the team's operations.
        investment: Initial investment amount for the team.
        idea: The idea or project the team is working on.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    env: Optional[Environment] = None
    investment: float = Field(default=10.0)
    idea: str = Field(default="")

    def __init__(self, context: Context = None, **data: Any):
        super(Team, self).__init__(**data)
        ctx = context or Context()
        if not self.env:
            self.env = Environment(context=ctx)
        else:
            self.env.context = ctx  # The `env` object is allocated by deserialization
        if "roles" in data:
            self.hire(data["roles"])
        if "env_desc" in data:
            self.env.desc = data["env_desc"]

    def serialize(self, stg_path: Path = None):
        """Serializes the team information to a specified storage path.

        Args:
            stg_path: The storage path where team information will be saved. If None, uses default path.
        """
        stg_path = SERDESER_PATH.joinpath("team") if stg_path is None else stg_path
        team_info_path = stg_path.joinpath("team.json")

        write_json_file(team_info_path, self.model_dump())

    @classmethod
    def deserialize(cls, stg_path: Path, context: Context = None) -> "Team":
        """Deserializes the team information from a specified storage path.

        Args:
            stg_path: The storage path where team information is saved.
            context: The context in which the team operates.

        Returns:
            An instance of `Team` loaded from the storage path.

        Raises:
            FileNotFoundError: If the `team.json` file does not exist at the specified path.
        """
        # recover team_info
        team_info_path = stg_path.joinpath("team.json")
        if not team_info_path.exists():
            raise FileNotFoundError(
                "recover storage meta file `team.json` not exist, " "not to recover and please start a new project."
            )

        team_info: dict = read_json_file(team_info_path)
        ctx = context or Context()
        team = Team(**team_info, context=ctx)
        return team

    def hire(self, roles: list[Role]):
        """Hires roles to cooperate with the team.

        Args:
            roles: A list of roles (agents) to be added to the team.
        """
        self.env.add_roles(roles)

    @property
    def cost_manager(self):
        """Gets the cost manager associated with the team.

        Returns:
            The cost manager of the team.
        """
        return self.env.context.cost_manager

    def invest(self, investment: float):
        """Invests in the team. Raises NoMoneyException when the investment exceeds the max budget.

        Args:
            investment: The amount to invest in the team.

        Raises:
            NoMoneyException: If the investment exceeds the max budget.
        """
        self.investment = investment
        self.cost_manager.max_budget = investment
        logger.info(f"Investment: ${investment}.")

    def _check_balance(self):
        if self.cost_manager.total_cost >= self.cost_manager.max_budget:
            raise NoMoneyException(self.cost_manager.total_cost, f"Insufficient funds: {self.cost_manager.max_budget}")

    def run_project(self, idea, send_to: str = ""):
        """Runs a project by publishing a user requirement.

        Args:
            idea: The idea or project to be run.
            send_to: The recipient of the message. If empty, sends to all.
        """
        self.idea = idea

        # Human requirement.
        self.env.publish_message(
            Message(role="Human", content=idea, cause_by=UserRequirement, send_to=send_to or MESSAGE_ROUTE_TO_ALL),
            peekable=False,
        )

    def start_project(self, idea, send_to: str = ""):
        """Deprecated: This method will be removed in the future. Use the `run_project` method instead.

        Args:
            idea: The idea or project to be started.
            send_to: The recipient of the message. If empty, sends to all.

        Deprecated:
            This method is deprecated and will be removed in the future. Use the `run_project` method instead.
        """
        warnings.warn(
            "The 'start_project' method is deprecated and will be removed in the future. "
            "Please use the 'run_project' method instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.run_project(idea=idea, send_to=send_to)

    def _save(self):
        logger.info(self.model_dump_json())

    @serialize_decorator
    async def run(self, n_round=3, idea="", send_to="", auto_archive=True):
        """Runs the team until the target round or until there's no money left.

        Args:
            n_round: The number of rounds to run the team for.
            idea: The idea or project to be run.
            send_to: The recipient of the message. If empty, sends to all.
            auto_archive: Whether to automatically archive the environment's history.

        Returns:
            The history of the environment after running.
        """
        if idea:
            self.run_project(idea=idea, send_to=send_to)

        while n_round > 0:
            # self._save()
            n_round -= 1
            logger.debug(f"max {n_round=} left.")
            self._check_balance()

            await self.env.run()
        self.env.archive(auto_archive)
        return self.env.history
