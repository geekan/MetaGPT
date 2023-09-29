#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : Stanford Town role

"""
Do the steps following:
- perceive, receive environment(Maze) info
- retrieve, retrieve memories
- plan, do plan like long-term plan and interact with Maze
- reflect, do the High-level thinking based on memories and re-add into the memory
- execute, move or else in the Maze
"""

from pydantic import Field
from pathlib import Path

from metagpt.roles.role import Role, RoleContext
from metagpt.schema import Message

from ..memory.agent_memory import AgentMemory
from ..actions.dummy_action import DummyAction
from ..actions.user_requirement import UserRequirement
from ..maze_environment import MazeEnvironment
from ..memory.retrieve import agent_retrieve
from ..memory.scratch import Scratch


class STRoleContext(RoleContext):
    env: 'MazeEnvironment' = Field(default=None)
    memory: AgentMemory = Field(default=AgentMemory)
    scratch: Scratch = Field(default=Scratch)


class STRole(Role):
    # 继承Role类，Role类继承RoleContext，这里的逻辑需要认真考虑
    # add a role's property structure to store role's age and so on like GA's Scratch.

    def __init__(self,
                 name: str = "Klaus Mueller",
                 profile: str = "STMember",
                 has_inner_voice: bool = False):

        self._rc = STRoleContext()
        super(STRole, self).__init__(name=name,
                                     profile=profile)

        self._init_actions([])

        if has_inner_voice:
            # TODO add communication action
            self._watch([UserRequirement, DummyAction])
        else:
            self._watch([DummyAction])

    def load_from(self, folder: Path):
        """
        load role data from `storage/{simulation_name}/personas/{role_name}
        """
        pass

    def save_into(self, folder: Path):
        """
        save role data from `storage/{simulation_name}/personas/{role_name}
        """
        pass

    async def observe(self):
        # TODO observe info from maze_env
        pass

    async def retrieve(self, query, n = 30 ,topk = 4):
        # TODO retrieve memories from agent_memory
        retrieve_memories = agent_retrieve(self._rc.memory, self._rc.scratch.curr_time, self._rc.scratch.recency_decay, query, n, topk)
        return retrieve_memories


    async def plan(self):
        # TODO make a plan

        # TODO judge if start a conversation

        # TODO update plan

        # TODO re-add result into memory
        pass

    async def reflect(self):
        # TODO reflection if meet reflect condition

        # TODO re-add result to memory
        pass

    async def _react(self) -> Message:
        maze_env = self._rc.env
        # TODO observe
        # get maze_env from self._rc.env, and observe env info

        # TODO retrieve, use self._rc.memory 's retrieve functions

        # TODO plan

        # TODO reflect

        # TODO execute(feed-back into maze_env)
