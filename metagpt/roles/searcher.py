#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/23 17:25
@Author  : alexanderwu
@File    : searcher.py
"""
from metagpt.actions import ActionOutput, SearchAndSummarize
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
    
    def __init__(self, 
                 name: str = 'Alice', 
                 profile: str = 'Smart Assistant', 
                 goal: str = 'Provide search services for users',
                 constraints: str = 'Answer is rich and complete', 
                 engine=SearchEngineType.SERPAPI_GOOGLE, 
                 **kwargs) -> None:
        """
        Initializes the Searcher role with given attributes.
        
        Args:
            name (str): Name of the searcher.
            profile (str): Role profile.
            goal (str): Goal of the searcher.
            constraints (str): Constraints or limitations for the searcher.
            engine (SearchEngineType): The type of search engine to use.
        """
        super().__init__(name, profile, goal, constraints, **kwargs)
        self._init_actions([SearchAndSummarize(engine=engine)])

    def set_search_func(self, search_func):
        """Sets a custom search function for the searcher."""
        action = SearchAndSummarize("", engine=SearchEngineType.CUSTOM_ENGINE, search_func=search_func)
        self._init_actions([action])

    async def _act_sp(self) -> Message:
        """Performs the search action in a single process."""
        logger.info(f"{self._setting}: ready to {self._rc.todo}")
        response = await self._rc.todo.run(self._rc.memory.get(k=0))
        
        if isinstance(response, ActionOutput):
            msg = Message(content=response.content, instruct_content=response.instruct_content,
                          role=self.profile, cause_by=type(self._rc.todo))
        else:
            msg = Message(content=response, role=self.profile, cause_by=type(self._rc.todo))
        self._rc.memory.add(msg)
        return msg

    async def _act(self) -> Message:
        """Determines the mode of action for the searcher."""
        return await self._act_sp()
