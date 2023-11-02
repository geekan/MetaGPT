#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 22:12
@Author  : alexanderwu
@File    : environment.py
@Modified By: mashenquan, 2023-11-1. Optimization:
    1. Remove the functionality of `Environment` class as a public message buffer.
    2. Standardize the message forwarding behavior of the `Environment` class.
    3. Add the `is_idle` property.
"""
import asyncio
from typing import Iterable

from pydantic import BaseModel, Field

from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message


class Environment(BaseModel):
    """环境，承载一批角色，角色可以向环境发布消息，可以被其他角色观察到
    Environment, hosting a batch of roles, roles can publish messages to the environment, and can be observed by other roles

    """

    roles: dict[str, Role] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    def add_role(self, role: Role):
        """增加一个在当前环境的角色
        Add a role in the current environment
        """
        role.set_env(self)
        self.roles[role.profile] = role

    def add_roles(self, roles: Iterable[Role]):
        """增加一批在当前环境的角色
        Add a batch of characters in the current environment
        """
        for role in roles:
            self.add_role(role)

    def publish_message(self, message: Message):
        """Distribute the message to the recipients."""
        logger.info(f"publish_message: {message.save()}")
        found = False
        for r in self.roles.values():
            if message.is_recipient(r.subscribed_tags):
                r.put_message(message)
                found = True
        if not found:
            logger.warning(f"Message no recipients: {message.save()}")

    async def run(self, k=1):
        """处理一次所有信息的运行
        Process all Role runs at once
        """
        for _ in range(k):
            futures = []
            for role in self.roles.values():
                future = role.run()
                futures.append(future)

            await asyncio.gather(*futures)
            logger.info(f"is idle: {self.is_idle}")

    def get_roles(self) -> dict[str, Role]:
        """获得环境内的所有角色
        Process all Role runs at once
        """
        return self.roles

    def get_role(self, name: str) -> Role:
        """获得环境内的指定角色
        get all the environment roles
        """
        return self.roles.get(name, None)

    @property
    def is_idle(self):
        """If true, all actions have been executed."""
        for r in self.roles.values():
            if not r.is_idle:
                return False
        return True
