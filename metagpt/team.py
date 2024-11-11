#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time		: 2023/5/12 00:30
@Author	: alexanderwu
@File		: team.py
@Modified By: mashenquan, 2023/11/27. Add an archiving operation after completing the project, as specified in
				Section 2.2.3.3 of RFC 135.
"""

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
from metagpt.gui_update_callback import gui_update_callback


class Team(BaseModel):
		"""
		Team: Possesses one or more roles (agents), SOP (Standard Operating Procedures), and a env for instant messaging,
		dedicated to env any multi-agent activity, such as collaboratively writing executable code.
		"""

		model_config = ConfigDict(arbitrary_types_allowed=True)

		env: Optional[Environment] = None
		investment: float = Field(default=10.0)
		idea: str = Field(default="")
		progress_callback: Optional[Any] = Field(default=gui_update_callback)
		ctx: Optional[Context] = Field(default=None)

		def __init__(self, context: Optional[Context] = None, **data: Any):
				# Initialize with all data first
				if context is not None:
						data['ctx'] = context
				elif 'ctx' not in data:
						data['ctx'] = Context()
				logger.info("Initializing Team with context and data.")
				super().__init__(**data)
				logger.debug(f"Context initialized: {self.ctx}")
				if not self.env:
						logger.info("No environment provided, creating a new Environment instance.")
						self.env = Environment()
						self.env.context = self.ctx
				else:
						self.env.context = self.ctx	# The `env` object is allocated by deserialization
				if "roles" in data:
						logger.info(f"=====Hiring roles: {[role.name for role in data['roles']]}")
						self.hire(data["roles"])
				if "env_desc" in data:
						logger.info(f"=====Setting environment description: {data['env_desc']}")
						self.env.desc = data["env_desc"]

		def serialize(self, stg_path: Path = None):
				stg_path = SERDESER_PATH.joinpath("team") if stg_path is None else stg_path
				team_info_path = stg_path.joinpath("team.json")
				serialized_data = self.model_dump()
				serialized_data["context"] = self.env.context.serialize()

				write_json_file(team_info_path, serialized_data)

		@classmethod
		def deserialize(cls, stg_path: Path, context: Context = None) -> "Team":
				"""stg_path = ./storage/team"""
				# recover team_info
				team_info_path = stg_path.joinpath("team.json")
				if not team_info_path.exists():
						raise FileNotFoundError(
								"recover storage meta file `team.json` not exist, " "not to recover and please start a new project."
						)

				team_info: dict = read_json_file(team_info_path)
				ctx = context or Context()
				ctx.deserialize(team_info.pop("context", None))
				team = Team(**team_info, context=ctx)
				return team

		def hire(self, roles: list[Role]):
				"""Hire roles to cooperate"""
				self.env.add_roles(roles)

		@property
		def cost_manager(self):
				"""Get cost manager"""
				return self.env.context.cost_manager

		def invest(self, investment: float):
				"""Invest company. raise NoMoneyException when exceed max_budget."""
				self.investment = investment
				self.cost_manager.max_budget = investment
				logger.info(f"Investment: ${investment}.")

		def _check_balance(self):
				if self.cost_manager.total_cost >= self.cost_manager.max_budget:
						raise NoMoneyException(self.cost_manager.total_cost, f"Insufficient funds: {self.cost_manager.max_budget}")

		def run_project(self, idea, send_to: str = ""):
				"""Run a project from publishing user requirement."""
				self.idea = idea

				# Human requirement.
				logger.info(f"=====Running project with idea: {idea}")
				self.env.publish_message(
						Message(role="Human", content=idea, cause_by=UserRequirement, send_to=send_to or MESSAGE_ROUTE_TO_ALL),
						peekable=False,
				)

		def start_project(self, idea, send_to: str = ""):
				"""
				Deprecated: This method will be removed in the future.
				Please use the `run_project` method instead.
				"""
				warnings.warn(
						"The 'start_project' method is deprecated and will be removed in the future. "
						"Please use the 'run_project' method instead.",
						DeprecationWarning,
						stacklevel=2,
				)
				return self.run_project(idea=idea, send_to=send_to)

		@serialize_decorator
		async def run(self, n_round: int = 3, idea: str = "", send_to: str = "", auto_archive: bool = True):
				"""Run company until target round or no money"""
				logger.info(f"=====Starting run with {n_round} rounds, idea: {idea}")
				if idea:
						self.run_project(idea=idea, send_to=send_to)

				while n_round > 0:
						logger.debug("Checking if environment is idle.")
						if self.env.is_idle:
								logger.debug("All roles are idle.")
								logger.info("All roles are idle, stopping execution.")
								break
						n_round -= 1
						logger.debug("Checking team balance.")
						self._check_balance()
						logger.info("==Executing environment run.")
						# Send thinking update before running
						if self.progress_callback:
								thinking_info = {
										"event": "thinking",
										"state": "processing",
										"actions": [str(getattr(role, 'actions', [])) for role in self.env.roles],
										"current_action": None,
										"history": [str(msg) for msg in self.env.history[-5:]]	# Last 5 messages
								}
								await self.progress_callback(thinking_info)
								await gui_update_callback(thinking_info)

						result = await self.env.run()
						
						if self.progress_callback:
								messages_data = []
								
								# Send acting update
								acting_info = {
										"event": "acting",
										"action": "team_execution",
										"description": f"Processing round {n_round}",
										"action_details": {"messages": len(result) if result else None}
								}
								await self.progress_callback(acting_info)
								await gui_update_callback(acting_info)
								if result:
									for msg in result:
										try:
												messages_data.append({
														"role": msg.role,
														"content": msg.content,
														"cause_by": str(msg.cause_by) if msg.cause_by else None,
														"send_to": msg.send_to
												})
										except Exception as e:
												logger.error(f"Error processing message: {e}")
												continue
												
								try:
										update_data = {
												"event": "team_progress",
												"round": n_round,
												"messages": messages_data
										}
										logger.debug(f"Sending progress update: {update_data}")
										await gui_update_callback(update_data)
										await self.progress_callback(update_data)
								except Exception as e:
										logger.error(f"Error in progress callback: {e}")

						logger.debug(f"max {n_round=} left.")
				logger.info("==Archiving environment state.")
				self.env.archive(auto_archive)
				return self.env.history
