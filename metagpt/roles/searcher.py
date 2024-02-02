#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/23 17:25
@Author  : alexanderwu
@File    : searcher.py
@Modified By: mashenquan, 2023-11-1. According to Chapter 2.2.1 and 2.2.2 of RFC 116, change the data type of
        the `cause_by` value in the `Message` to a string to support the new message distribution feature.
"""

from typing import Optional

from pydantic import Field, model_validator

from metagpt.actions import SearchAndSummarize
from metagpt.actions.action_node import ActionNode
from metagpt.actions.action_output import ActionOutput
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.tools.search_engine import SearchEngine


class Searcher(Role):
    """
    Represents a Searcher role responsible for providing search services to users.

    Attributes:
        name (str): Name of the searcher.
        profile (str): Role profile.
        goal (str): Goal of the searcher.
        constraints (str): Constraints or limitations for the searcher.
        search_engine (SearchEngine): The search engine to use.
    """

    name: str = Field(default="Alice")
    profile: str = Field(default="Smart Assistant")
    goal: str = "Provide search services for users"
    constraints: str = "Answer is rich and complete"
    search_engine: Optional[SearchEngine] = None

    @model_validator(mode="after")
    def post_root(self):
        if self.search_engine:
            self.set_actions([SearchAndSummarize(search_engine=self.search_engine, context=self.context)])
        else:
            self.set_actions([SearchAndSummarize])
        return self

    async def _act_sp(self) -> Message:
        """Performs the search action in a single process."""
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        response = await self.rc.todo.run(self.rc.memory.get(k=0))

        if isinstance(response, (ActionOutput, ActionNode)):
            msg = Message(
                content=response.content,
                instruct_content=response.instruct_content,
                role=self.profile,
                cause_by=self.rc.todo,
            )
        else:
            msg = Message(content=response, role=self.profile, cause_by=self.rc.todo)
        self.rc.memory.add(msg)
        return msg

    async def _act(self) -> Message:
        """Determines the mode of action for the searcher."""
        return await self._act_sp()
