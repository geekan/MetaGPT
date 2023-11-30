#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 22:12
@Author  : alexanderwu
@File    : environment.py
@Modified By: mashenquan, 2023-11-1. According to Chapter 2.2.2 of RFC 116:
    1. Remove the functionality of `Environment` class as a public message buffer.
    2. Standardize the message forwarding behavior of the `Environment` class.
    3. Add the `is_idle` property.
@Modified By: mashenquan, 2023-11-4. According to the routing feature plan in Chapter 2.2.3.2 of RFC 113, the routing
    functionality is to be consolidated into the `Environment` class.
"""
import asyncio
from typing import Iterable, Set
from pathlib import Path

from pydantic import BaseModel, Field

from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.memory import Memory
from metagpt.roles.role import Role, role_subclass_registry
from metagpt.schema import Message
from metagpt.utils.common import is_subscribed
from metagpt.utils.utils import read_json_file, write_json_file


class Environment(BaseModel):
    """环境，承载一批角色，角色可以向环境发布消息，可以被其他角色观察到
    Environment, hosting a batch of roles, roles can publish messages to the environment, and can be observed by other roles

    """

    roles: dict[str, Role] = Field(default_factory=dict)
    members: dict[Role, Set] = Field(default_factory=dict)
    history: str = Field(default="")  # For debug

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
        """ stg_path: ./storage/team/environment/ """
        roles_path = stg_path.joinpath("roles.json")
        roles_info = read_json_file(roles_path)
        roles = []
        for role_info in roles_info:
            # role stored in ./environment/roles/{role_class}_{role_name}
            role_path = stg_path.joinpath(f'roles/{role_info.get("role_class")}_{role_info.get("role_name")}')
            role = Role.deserialize(role_path)
            roles.append(role)

        history = read_json_file(stg_path.joinpath("history.json"))
        history = history.get("content")

        environment = Environment(**{
            "history": history
        })
        environment.add_roles(roles)
        return environment

    def add_role(self, role: Role):
        """增加一个在当前环境的角色
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

    def publish_message(self, message: Message) -> bool:
        """
        Distribute the message to the recipients.
        In accordance with the Message routing structure design in Chapter 2.2.1 of RFC 116, as already planned
        in RFC 113 for the entire system, the routing information in the Message is only responsible for
        specifying the message recipient, without concern for where the message recipient is located. How to
        route the message to the message recipient is a problem addressed by the transport framework designed
        in RFC 113.
        """
        logger.debug(f"publish_message: {message.dump()}")
        found = False
        # According to the routing feature plan in Chapter 2.2.3.2 of RFC 113
        for role, subscription in self.members.items():
            if is_subscribed(message, subscription):
                role.put_message(message)
                found = True
        if not found:
            logger.warning(f"Message no recipients: {message.dump()}")
        self.history += f"\n{message}"  # For debug

        return True

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
            logger.debug(f"is idle: {self.is_idle}")

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

    def get_subscription(self, obj):
        """Get the labels for messages to be consumed by the object."""
        return self.members.get(obj, {})

    def set_subscription(self, obj, tags):
        """Set the labels for message to be consumed by the object"""
        self.members[obj] = tags
