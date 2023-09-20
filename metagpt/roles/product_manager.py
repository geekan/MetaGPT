#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : product_manager.py
"""
from metagpt.actions import BossRequirement, WritePRD, Feedback
from metagpt.roles import Role
from metagpt.logs import logger
from metagpt.schema import Message

class ProductManager(Role):
    """
    Represents a Product Manager role responsible for product development and management.
    
    Attributes:
        name (str): Name of the product manager.
        profile (str): Role profile, default is 'Product Manager'.
        goal (str): Goal of the product manager.
        constraints (str): Constraints or limitations for the product manager.
    """
    
    def __init__(self, 
                 name: str = "Alice", 
                 profile: str = "Product Manager", 
                 goal: str = "Efficiently create a successful product",
                 constraints: str = "",
                 feedback: bool = True) -> None:
        """
        Initializes the ProductManager role with given attributes.
        
        Args:
            name (str): Name of the product manager.
            profile (str): Role profile.
            goal (str): Goal of the product manager.
            constraints (str): Constraints or limitations for the product manager.
        """
        super().__init__(name, profile, goal, constraints, feedback)
        self._init_actions([WritePRD])
        if feedback:
            self._init_actions([Feedback, WritePRD])
        self._watch([BossRequirement])

    async def _think(self) -> None:

        if self._rc.todo is None:
            self._set_state(0)
            return

        if self._rc.state + 1 < len(self._states):
            self._set_state(self._rc.state + 1)
        else:
            self._rc.todo = None

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self._rc.todo}")
        todo = self._rc.todo
        
        if isinstance(todo, Feedback):
            msg = self._rc.memory.get_by_action(BossRequirement)
            feedback =  await todo.run(msg)
            ret = Message(feedback, role=self.profile, cause_by=type(todo))
        elif isinstance(todo, WritePRD):
            msg = self._rc.memory.get_by_action(BossRequirement)
            prd =  await todo.run(msg)
            ret = Message(prd.content, role=self.profile, cause_by=WritePRD)
        else:
            raise NotImplementedError
        
        self._rc.memory.add(ret)
        return ret
    
    async def _react(self) -> Message:
        while True:
            await self._think()
            if self._rc.todo is None:
                break
            msg = await self._act()
            todo = self._rc.todo
            ret = Message(msg, role=self.profile, cause_by=type(todo))

        return ret