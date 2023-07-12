#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 22:12
@Author  : alexanderwu
@File    : environment.py
"""
import asyncio

from typing import Iterable

from pydantic import (
    BaseModel,
    BaseSettings,
    PyObject,
    RedisDsn,
    PostgresDsn,
    Field,
)

from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.memory import Memory


class Environment(BaseModel):
    """环境，承载一批角色，角色可以向环境发布消息，可以被其他角色观察到"""

    roles: dict[str, Role] = Field(default_factory=dict)
    memory: Memory = Field(default_factory=Memory)
    history: str = Field(default='')

    class Config:
        arbitrary_types_allowed = True

    def add_role(self, role: Role):
        """增加一个在当前环境的Role"""
        role.set_env(self)
        self.roles[role.profile] = role

    def add_roles(self, roles: Iterable[Role]):
        """增加一批在当前环境的Role"""
        for role in roles:
            self.add_role(role)

    def publish_message(self, message: Message):
        """向当前环境发布信息"""
        # self.message_queue.put(message)
        self.memory.add(message)
        self.history += f"\n{message}"

    async def run(self, k=1):
        """处理一次所有Role的运行"""
        # while not self.message_queue.empty():
        # message = self.message_queue.get()
        # rsp = await self.manager.handle(message, self)
        # self.message_queue.put(rsp)
        for _ in range(k):
            futures = []
            for role in self.roles.values():
                future = role.run()
                futures.append(future)

            await asyncio.gather(*futures)

    def get_roles(self) -> dict[str, Role]:
        """获得环境内的所有Role"""
        return self.roles

    def get_role(self, name: str) -> Role:
        """获得环境内的指定Role"""
        return self.roles.get(name, None)
