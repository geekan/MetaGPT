#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : base env of executing environment

import asyncio
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional, Set, Union

from pydantic import BaseModel, ConfigDict, Field, SerializeAsAny, model_validator

from metagpt.context import Context
from metagpt.environment.api.env_api import (
    EnvAPIAbstract,
    ReadAPIRegistry,
    WriteAPIRegistry,
)
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.utils.common import get_function_schema, is_coroutine_func, is_send_to

if TYPE_CHECKING:
    from metagpt.roles.role import Role  # noqa: F401


class EnvType(Enum):
    ANDROID = "Android"
    GYM = "Gym"
    WEREWOLF = "Werewolf"
    MINCRAFT = "Mincraft"
    STANFORDTOWN = "StanfordTown"


env_write_api_registry = WriteAPIRegistry()
env_read_api_registry = ReadAPIRegistry()


def mark_as_readable(func):
    """mark functionn as a readable one in ExtEnv, it observes something from ExtEnv"""
    env_read_api_registry[func.__name__] = get_function_schema(func)
    return func


def mark_as_writeable(func):
    """mark functionn as a writeable one in ExtEnv, it does something to ExtEnv"""
    env_write_api_registry[func.__name__] = get_function_schema(func)
    return func


class ExtEnv(BaseModel):
    """External Env to intergate actual game environment"""

    def _check_api_exist(self, rw_api: Optional[str] = None):
        if not rw_api:
            raise ValueError(f"{rw_api} not exists")

    def get_all_available_apis(self, mode: str = "read") -> list[Any]:
        """get available read/write apis definition"""
        assert mode in ["read", "write"]
        if mode == "read":
            return env_read_api_registry.get_apis()
        else:
            return env_write_api_registry.get_apis()

    async def observe(self, env_action: Union[str, EnvAPIAbstract]):
        """get observation from particular api of ExtEnv"""
        if isinstance(env_action, str):
            read_api = env_read_api_registry.get(api_name=env_action)["func"]
            self._check_api_exist(read_api)
            if is_coroutine_func(read_api):
                res = await read_api(self)
            else:
                res = read_api(self)
        elif isinstance(env_action, EnvAPIAbstract):
            read_api = env_read_api_registry.get(api_name=env_action.api_name)["func"]
            self._check_api_exist(read_api)
            if is_coroutine_func(read_api):
                res = await read_api(self, *env_action.args, **env_action.kwargs)
            else:
                res = read_api(self, *env_action.args, **env_action.kwargs)
        return res

    async def step(self, env_action: Union[str, Message, EnvAPIAbstract, list[EnvAPIAbstract]]):
        """execute through particular api of ExtEnv"""
        res = None
        if isinstance(env_action, Message):
            self.publish_message(env_action)
        elif isinstance(env_action, EnvAPIAbstract):
            write_api = env_write_api_registry.get(env_action.api_name)["func"]
            self._check_api_exist(write_api)
            if is_coroutine_func(write_api):
                res = await write_api(self, *env_action.args, **env_action.kwargs)
            else:
                res = write_api(self, *env_action.args, **env_action.kwargs)

        return res


class Environment(ExtEnv):
    """环境，承载一批角色，角色可以向环境发布消息，可以被其他角色观察到
    Environment, hosting a batch of roles, roles can publish messages to the environment, and can be observed by other roles
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    desc: str = Field(default="")  # 环境描述
    roles: dict[str, SerializeAsAny["Role"]] = Field(default_factory=dict, validate_default=True)
    member_addrs: Dict["Role", Set] = Field(default_factory=dict, exclude=True)
    history: str = ""  # For debug
    context: Context = Field(default_factory=Context, exclude=True)

    @model_validator(mode="after")
    def init_roles(self):
        self.add_roles(self.roles.values())
        return self

    def add_role(self, role: "Role"):
        """增加一个在当前环境的角色
        Add a role in the current environment
        """
        self.roles[role.profile] = role
        role.set_env(self)
        role.context = self.context

    def add_roles(self, roles: Iterable["Role"]):
        """增加一批在当前环境的角色
        Add a batch of characters in the current environment
        """
        for role in roles:
            self.roles[role.profile] = role

        for role in roles:  # setup system message with roles
            role.set_env(self)
            role.context = self.context

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
        for role, addrs in self.member_addrs.items():
            if is_send_to(message, addrs):
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

    def get_roles(self) -> dict[str, "Role"]:
        """获得环境内的所有角色
        Process all Role runs at once
        """
        return self.roles

    def get_role(self, name: str) -> "Role":
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

    def get_addresses(self, obj):
        """Get the addresses of the object."""
        return self.member_addrs.get(obj, {})

    def set_addresses(self, obj, addresses):
        """Set the addresses of the object"""
        self.member_addrs[obj] = addresses

    def archive(self, auto_archive=True):
        if auto_archive and self.context.git_repo:
            self.context.git_repo.archive()

    @classmethod
    def model_rebuild(cls, **kwargs):
        from metagpt.roles.role import Role  # noqa: F401

        super().model_rebuild(**kwargs)


Environment.model_rebuild()
