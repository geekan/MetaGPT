#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/5/11 22:12
# @Author  : alexanderwu
# @File    : environment.py
# @Modified By: mashenquan, 2023-11-1. According to Chapter 2.2.2 of RFC 116:
#     1. Remove the functionality of `Environment` class as a public message buffer.
#     2. Standardize the message forwarding behavior of the `Environment` class.
#     3. Add the `is_idle` property.
# @Modified By: mashenquan, 2023-11-4. According to the routing feature plan in Chapter 2.2.3.2 of RFC 113, the routing
#     functionality is to be consolidated into the `Environment` class.

import asyncio
from typing import Iterable, Set

from pydantic import BaseModel, ConfigDict, Field, SerializeAsAny, model_validator

from metagpt.context import Context
from metagpt.logs import logger
from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.utils.common import is_send_to


class Environment(BaseModel):
    """Environment, hosting a batch of roles, roles can publish messages to the environment, and can be observed by other roles."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    desc: str = Field(default="")  # 环境描述
    roles: dict[str, SerializeAsAny[Role]] = Field(default_factory=dict, validate_default=True)
    member_addrs: dict[Role, Set] = Field(default_factory=dict, exclude=True)
    history: str = ""  # For debug
    context: Context = Field(default_factory=Context, exclude=True)

    @model_validator(mode="after")
    def init_roles(self):
        self.add_roles(self.roles.values())
        return self

    def add_role(self, role: Role):
        """Add a role in the current environment."""
        self.roles[role.profile] = role
        role.set_env(self)
        role.context = self.context

    def add_roles(self, roles: Iterable[Role]):
        """Add a batch of characters in the current environment."""
        for role in roles:
            self.roles[role.profile] = role

        for role in roles:  # setup system message with roles
            role.set_env(self)
            role.context = self.context

    def publish_message(self, message: Message, peekable: bool = True) -> bool:
        """Distribute the message to the recipients.

        In accordance with the Message routing structure design in Chapter 2.2.1 of RFC 116, as already planned
        in RFC 113 for the entire system, the routing information in the Message is only responsible for
        specifying the message recipient, without concern for where the message recipient is located. How to
        route the message to the message recipient is a problem addressed by the transport framework designed
        in RFC 113.
        """
        logger.debug(f"publish_message: {message.dump()}")
        found = False
        # According to the routing feature plan in Chapter 2.2.3.2 of RFC 113
        for role, addrs in self.member_addrs.items():
            if is_send_to(message, addrs):
                role.put_message(message)
                found = True
        if not found:
            logger.warning(f"Message no recipients: {message.dump()}")
        self.history += f"\n{message}"  # For debug

        return True

    async def run(self, k=1):
        """Process all Role runs at once."""
        for _ in range(k):
            futures = []
            for role in self.roles.values():
                future = role.run()
                futures.append(future)

            await asyncio.gather(*futures)
            logger.debug(f"is idle: {self.is_idle}")

    def get_roles(self) -> dict[str, Role]:
        """Process all Role runs at once."""
        return self.roles

    def get_role(self, name: str) -> Role:
        """Get all the environment roles."""
        return self.roles.get(name, None)

    def role_names(self) -> list[str]:
        """Get the names of all roles in the environment."""
        return [i.name for i in self.roles.values()]

    @property
    def is_idle(self):
        """If true, all actions have been executed."""
        for r in self.roles.values():
            if not r.is_idle:
                return False
        return True

    def get_addresses(self, obj):
        """Get the addresses of the object."""
        return self.member_addrs.get(obj, {})

    def set_addresses(self, obj, addresses):
        """Set the addresses of the object."""
        self.member_addrs[obj] = addresses

    def archive(self, auto_archive=True):
        """Archive the environment's state if auto_archive is True and a git repository is associated."""
        if auto_archive and self.context.git_repo:
            self.context.git_repo.archive()
