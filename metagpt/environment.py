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
from pathlib import Path
from typing import Iterable, Set

from pydantic import BaseModel, ConfigDict, Field, SerializeAsAny, model_validator

from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.utils.common import is_subscribed, read_json_file, write_json_file


class Environment(BaseModel):
    """环境，承载一批角色，角色可以向环境发布消息，可以被其他角色观察到
    Environment, hosting a batch of roles, roles can publish messages to the environment, and can be observed by other roles
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    desc: str = Field(default="")  # 环境描述
    roles: dict[str, SerializeAsAny[Role]] = Field(default_factory=dict, validate_default=True)
    members: dict[Role, Set] = Field(default_factory=dict, exclude=True)
    history: str = ""  # For debug

    @model_validator(mode="after")
    def init_roles(self):
        self.add_roles(self.roles.values())
        return self

    def serialize(self, stg_path: Path):
        roles_path = stg_path.joinpath("roles.json")
        roles_info = []
        for role_key, role in self.roles.items():
            roles_info.append(
                {
                    "role_class": role.__class__.__name__,
                    "module_name": role.__module__,
                    "role_name": role.name,
                    "role_sub_tags": list(self.members.get(role)),
                }
            )
            role.serialize(stg_path=stg_path.joinpath(f"roles/{role.__class__.__name__}_{role.name}"))
        write_json_file(roles_path, roles_info)

        history_path = stg_path.joinpath("history.json")
        write_json_file(history_path, {"content": self.history})

    @classmethod
    def deserialize(cls, stg_path: Path) -> "Environment":
        """stg_path: ./storage/team/environment/"""
        roles_path = stg_path.joinpath("roles.json")
        roles_info = read_json_file(roles_path)
        roles = []
        for role_info in roles_info:
            # role stored in ./environment/roles/{role_class}_{role_name}
            role_path = stg_path.joinpath(f"roles/{role_info.get('role_class')}_{role_info.get('role_name')}")
            role = Role.deserialize(role_path)
            roles.append(role)

        history = read_json_file(stg_path.joinpath("history.json"))
        history = history.get("content")

        environment = Environment(**{"history": history})
        environment.add_roles(roles)

        return environment

    def add_role(self, role: Role):
        """增加一个在当前环境的角色
        Add a role in the current environment
        """
        self.roles[role.profile] = role
        role.set_env(self)

    def add_roles(self, roles: Iterable[Role]):
        """增加一批在当前环境的角色
        Add a batch of characters in the current environment
        """
        for role in roles:
            self.roles[role.profile] = role

        for role in roles:  # setup system message with roles
            role.set_env(self)

    def publish_message(self, message: Message, peekable: bool = True) -> bool:
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

    def role_names(self) -> list[str]:
        return [i.name for i in self.roles.values()]

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

    @staticmethod
    def archive(auto_archive=True):
        if auto_archive and CONFIG.git_repo:
            CONFIG.git_repo.archive()
