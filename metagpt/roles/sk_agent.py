#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/13 12:23
@Author  : femto Zheng
@File    : sk_agent.py
"""
import os

from semantic_kernel.core_skills.text_skill import TextSkill
from semantic_kernel.planning.basic_planner import BasicPlanner

from metagpt.actions import BossRequirement
from metagpt.actions.execute_task import ExecuteTask
from metagpt.logs import logger
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

    def __init__(
        self,
        name: str = "Sunshine",
        profile: str = "sk_agent",
        goal: str = "Execute task based on passed in task description",
        constraints: str = "",
        planner=BasicPlanner(),
    ) -> None:
        """Initializes the Engineer role with given attributes."""
        super().__init__(name, profile, goal, constraints)
        self._init_actions([ExecuteTask(role=self)])
        self._watch([BossRequirement])
        self.kernel = make_sk_kernel()
        self.planner = planner

        # Get the directory of the current file
        current_file_directory = os.path.dirname(os.path.abspath(__file__))

        # Construct the skills_directory by joining the parent directory and "skillss"
        skills_directory = os.path.join(current_file_directory, "..", "skills")

        # Normalize the path to ensure it's in the correct format
        skills_directory = os.path.normpath(skills_directory)

        self.kernel.import_semantic_skill_from_directory(skills_directory, "SummarizeSkill")
        self.kernel.import_semantic_skill_from_directory(skills_directory, "WriterSkill")
        self.kernel.import_skill(TextSkill(), "TextSkill")

    async def _think(self) -> None:
        self.plan = await self.planner.create_plan_async(self._rc.important_memory[-1].content, self.kernel)
        logger.info(self.plan.generated_plan)
        # for step in self.plan._steps:
        #     print(step.description, ":", step._state.__dict__)

    async def _act(self) -> Message:
        # result = await self.planner.execute_plan_async(self.plan, self.kernel)
        result = await self.plan.invoke_async()
        logger.info(result)
        return Message(content=result)
