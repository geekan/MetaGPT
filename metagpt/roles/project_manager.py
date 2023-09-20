#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 15:04
@Author  : alexanderwu
@File    : project_manager.py
"""
from metagpt.actions import WriteDesign, WriteTasks, Feedback
from metagpt.roles import Role
from metagpt.logs import logger
from metagpt.schema import Message

class ProjectManager(Role):
    """
    Represents a Project Manager role responsible for overseeing project execution and team efficiency.
    
    Attributes:
        name (str): Name of the project manager.
        profile (str): Role profile, default is 'Project Manager'.
        goal (str): Goal of the project manager.
        constraints (str): Constraints or limitations for the project manager.
    """
    
    def __init__(self, 
                 name: str = "Eve", 
                 profile: str = "Project Manager", 
                 goal: str = "Improve team efficiency and deliver with quality and quantity",
                 constraints: str = "",
                 feedback: bool = True) -> None:
        """
        Initializes the ProjectManager role with given attributes.
        
        Args:
            name (str): Name of the project manager.
            profile (str): Role profile.
            goal (str): Goal of the project manager.
            constraints (str): Constraints or limitations for the project manager.
        """
        super().__init__(name, profile, goal, constraints, feedback)
        # Initialize actions specific to the ProjectManager role
        self._init_actions([WriteTasks])
        if feedback:
            self._add_action_at_head(Feedback)
        # Set events or actions the ProjectManager should watch or be aware of
        self._watch([WriteDesign])

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
            msg = self._rc.memory.get_by_action(WriteDesign)[0]
            feedback =  await todo.run(msg)
            ret = Message(feedback, role=self.profile, cause_by=type(todo))
        elif isinstance(todo, WriteTasks):
            msg = self._rc.memory.get_by_action(WriteDesign)
            tasks =  await todo.run(msg)
            ret = Message(tasks.content, role=self.profile, cause_by=WriteTasks)
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
            ret = Message(msg.content, role=self.profile, cause_by=type(todo)) #.content?

        return ret