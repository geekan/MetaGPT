#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/13 12:23
@Author  : femto Zheng
@File    : sk_agent.py
@Modified By: mashenquan, 2023-11-1. In accordance with Chapter 2.2.1 and 2.2.2 of RFC 116, utilize the new message
        distribution feature for message filtering.
"""

from pydantic import Field
from semantic_kernel.planning import SequentialPlanner
from semantic_kernel.planning.action_planner.action_planner import ActionPlanner
from semantic_kernel.planning.basic_planner import BasicPlanner

from metagpt.actions import UserRequirement
from metagpt.actions.execute_task import ExecuteTask
from metagpt.llm import LLM
from metagpt.provider.base_gpt_api import BaseGPTAPI
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.utils.make_sk_kernel import make_sk_kernel


class SkAgent(Role):
    """
    Represents an SkAgent implemented using semantic kernel

    Attributes:
        name (str): Name of the SkAgent.
        profile (str): Role profile, default is 'sk_agent'.
        goal (str): Goal of the SkAgent.
        constraints (str): Constraints for the SkAgent.
    """

    name: str = "Sunshine"
    profile: str = "sk_agent"
    goal: str = "Execute task based on passed in task description"
    constraints: str = ""
    planner_cls: BasicPlanner = BasicPlanner
    planner: BasicPlanner = Field(default_factory=BasicPlanner)
    llm: BaseGPTAPI = Field(default_factory=LLM)

    def __init__(self, **kwargs) -> None:
        """Initializes the Engineer role with given attributes."""
        super().__init__(**kwargs)
        self._init_actions([ExecuteTask()])
        self._watch([UserRequirement])
        self.kernel = make_sk_kernel()

        # how funny the interface is inconsistent
        if self.planner_cls == BasicPlanner:
            self.planner = self.planner_cls()
        elif self.planner_cls in [SequentialPlanner, ActionPlanner]:
            self.planner = self.planner_cls(self.kernel)
        else:
            raise Exception(f"Unsupported planner of type {self.planner_cls}")

        self.import_semantic_skill_from_directory = self.kernel.import_semantic_skill_from_directory
        self.import_skill = self.kernel.import_skill

    async def _think(self) -> None:
        self._set_state(0)
        # how funny the interface is inconsistent
        if isinstance(self.planner, BasicPlanner):
            self.plan = await self.planner.create_plan_async(self._rc.important_memory[-1].content, self.kernel)
            logger.info(self.plan.generated_plan)
        elif any(isinstance(self.planner, cls) for cls in [SequentialPlanner, ActionPlanner]):
            self.plan = await self.planner.create_plan_async(self._rc.important_memory[-1].content)

    async def _act(self) -> Message:
        # how funny the interface is inconsistent
        if isinstance(self.planner, BasicPlanner):
            result = await self.planner.execute_plan_async(self.plan, self.kernel)
        elif any(isinstance(self.planner, cls) for cls in [SequentialPlanner, ActionPlanner]):
            result = (await self.plan.invoke_async()).result
        logger.info(result)

        msg = Message(content=result, role=self.profile, cause_by=self._rc.todo)
        self._rc.memory.add(msg)
        return msg
