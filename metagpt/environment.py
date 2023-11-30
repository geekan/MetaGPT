#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 22:12
@Author  : alexanderwu
@File    : environment.py
"""
import asyncio
from typing import Iterable
from pathlib import Path

from pydantic import BaseModel, Field

from metagpt.memory import Memory
from metagpt.roles.role import Role, role_subclass_registry
from metagpt.schema import Message
from metagpt.utils.utils import read_json_file, write_json_file


class Environment(BaseModel):
    """环境，承载一批角色，角色可以向环境发布消息，可以被其他角色观察到
       Environment, hosting a batch of roles, roles can publish messages to the environment, and can be observed by other roles
    
    """

    roles: dict[str, Role] = Field(default_factory=dict)
    memory: Memory = Field(default_factory=Memory)
    history: str = Field(default='')

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        roles = []
        for role_key, role in kwargs.get("roles", {}).items():
            current_role = kwargs["roles"][role_key]
            if isinstance(current_role, dict):
                item_class_name = current_role.get("builtin_class_name", None)
                for name, subclass in role_subclass_registry.items():
                    registery_class_name = subclass.__fields__["builtin_class_name"].default
                    if item_class_name == registery_class_name:
                        current_role = subclass(**current_role)
                        break
                kwargs["roles"][role_key] = current_role
                roles.append(current_role)
        super().__init__(**kwargs)

        self.add_roles(roles)  # add_roles again to init the Role.set_env

    def serialize(self, stg_path: Path):
        roles_path = stg_path.joinpath("roles.json")
        roles_info = []
        for role_key, role in self.roles.items():
            roles_info.append({
                "role_class": role.__class__.__name__,
                "module_name": role.__module__,
                "role_name": role.name
            })
            role.serialize(stg_path=stg_path.joinpath(f"roles/{role.__class__.__name__}_{role.name}"))
        write_json_file(roles_path, roles_info)

        self.memory.serialize(stg_path)
        history_path = stg_path.joinpath("history.json")
        write_json_file(history_path, {"content": self.history})

    @classmethod
    def deserialize(cls, stg_path: Path) -> "Environment":
        """ stg_path: ./storage/team/environment/ """
        roles_path = stg_path.joinpath("roles.json")
        roles_info = read_json_file(roles_path)
        roles = []
        for role_info in roles_info:
            role_class = role_info.get("role_class")
            role_name = role_info.get("role_name")

            role_path = stg_path.joinpath(f"roles/{role_class}_{role_name}")
            role = Role.deserialize(role_path)
            roles.append(role)

        memory = Memory.deserialize(stg_path)

        history = read_json_file(stg_path.joinpath("history.json"))
        history = history.get("content")

        environment = Environment(**{
            "memory": memory,
            "history": history
        })
        environment.add_roles(roles)
        return environment

    def add_role(self, role: Role):
        """增加一个在当前环境的角色, 默认为profile
           Add a role in the current environment
        """
        role.set_env(self)
        # use alias
        self.roles[role.profile] = role

    def add_roles(self, roles: Iterable[Role]):
        """增加一批在当前环境的角色
            Add a batch of characters in the current environment
        """
        for role in roles:
            self.add_role(role)

    def publish_message(self, message: Message):
        """向当前环境发布信息
          Post information to the current environment
        """
        # self.message_queue.put(message)
        self.memory.add(message)
        self.history += f"\n{message}"

    async def run(self, k=1):
        """处理一次所有信息的运行
        Process all Role runs at once
        """
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
        """获得环境内的所有角色
           Process all Role runs at once
        """
        return self.roles

    def get_role(self, name: str) -> Role:
        """获得环境内的指定角色
           get all the environment roles
        """
        return self.roles.get(name, None)
