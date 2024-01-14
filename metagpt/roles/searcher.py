#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/23 17:25
@Author  : alexanderwu
@File    : searcher.py
@Modified By: mashenquan, 2023-11-1. According to Chapter 2.2.1 and 2.2.2 of RFC 116, change the data type of
        the `cause_by` value in the `Message` to a string to support the new message distribution feature.
"""

from pydantic import Field

from metagpt.actions import ActionOutput, SearchAndSummarize
from metagpt.actions.action_node import ActionNode
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.tools import SearchEngineType


class Searcher(Role):
    """
    Represents a Searcher role responsible for providing search services to users.

    Attributes:
        name (str): Name of the searcher.
        profile (str): Role profile.
        goal (str): Goal of the searcher.
        constraints (str): Constraints or limitations for the searcher.
        engine (SearchEngineType): The type of search engine to use.
    """

    name: str = Field(default="Alice")
    profile: str = Field(default="Smart Assistant")
    goal: str = "Provide search services for users"
    constraints: str = "Answer is rich and complete"
    engine: SearchEngineType = SearchEngineType.SERPAPI_GOOGLE

    def __init__(self, **kwargs) -> None:
        """
        Initializes the Searcher role with given attributes.

        Args:
            name (str): Name of the searcher.
            profile (str): Role profile.
            goal (str): Goal of the searcher.
            constraints (str): Constraints or limitations for the searcher.
            engine (SearchEngineType): The type of search engine to use.
        """
        super().__init__(**kwargs)
        self._init_actions([SearchAndSummarize(engine=self.engine)])

    def set_search_func(self, search_func):
        """Sets a custom search function for the searcher."""
        action = SearchAndSummarize(name="", engine=SearchEngineType.CUSTOM_ENGINE, search_func=search_func)
        self._init_actions([action])

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
