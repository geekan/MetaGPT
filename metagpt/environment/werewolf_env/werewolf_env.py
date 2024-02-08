#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : MG Werewolf Env

from pydantic import Field

from metagpt.environment.base_env import Environment
from metagpt.environment.werewolf_env.werewolf_ext_env import WerewolfExtEnv
from metagpt.logs import logger
from metagpt.schema import Message


class WerewolfEnv(Environment, WerewolfExtEnv):
    timestamp: int = Field(default=0)

    def publish_message(self, message: Message, add_timestamp: bool = True):
        """Post information to the current environment"""
        logger.debug(f"publish_message: {message.dump()}")
        if add_timestamp:
            # Because the content of the message may be repeated, for example, killing the same person in two nights
            # Therefore, a unique timestamp prefix needs to be added so that the same message will not be automatically deduplicated when added to the memory.
            message.content = f"{self.timestamp} | " + message.content
        self.memory.add(message)
        self.history += f"\n{message}"

    async def run(self, k=1):
        """Process all Role runs by order"""
        for _ in range(k):
            for role in self.roles.values():
                await role.run()
            self.timestamp += 1
