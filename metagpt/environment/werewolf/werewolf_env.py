#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : MG Werewolf Env

from typing import Iterable

from pydantic import Field

from metagpt.environment.base_env import Environment
from metagpt.environment.werewolf.werewolf_ext_env import WerewolfExtEnv
from metagpt.schema import Message


class WerewolfEnv(WerewolfExtEnv, Environment):
    round_cnt: int = Field(default=0)

    def add_roles(self, roles: Iterable["Role"]):
        """增加一批在当前环境的角色
        Add a batch of characters in the current environment
        """
        for role in roles:
            self.roles[role.name] = role  # use name as key here, due to multi-player can have same profile

        for role in roles:  # setup system message with roles
            role.context = self.context
            role.set_env(self)

    def publish_message(self, message: Message, add_timestamp: bool = True):
        """Post information to the current environment"""
        if add_timestamp:
            # Because the content of the message may be repeated, for example, killing the same person in two nights
            # Therefore, a unique round_cnt prefix needs to be added so that the same message will not be automatically deduplicated when added to the memory.
            message.content = f"{self.round_cnt} | " + message.content
        super().publish_message(message)

    async def run(self, k=1):
        """Process all Role runs by order"""
        for _ in range(k):
            for role in self.roles.values():
                await role.run()
            self.round_cnt += 1
