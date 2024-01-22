#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : base env of executing environment

from enum import Enum
from typing import Union

from pydantic import BaseModel, ConfigDict, Field

from metagpt.env.api.env_api import EnvAPIAbstract, ReadAPIRegistry, WriteAPIRegistry
from metagpt.schema import Message


class EnvType(Enum):
    ANDROID = "Android"
    GYM = "Gym"
    WEREWOLF = "Werewolf"
    MINCRAFT = "Minsraft"
    STANFORDTOWN = "StanfordTown"


def mark_as_readable(func):
    """mark functionn as a readable one in ExtEnv, it observes something from ExtEnv"""

    def wrapper(self: ExtEnv, *args, **kwargs):
        api_name = str(func)  # TODO
        self.read_api_registry[api_name] = func
        return func(self, *args, **kwargs)

    return wrapper


def mark_as_writeable(func):
    """mark functionn as a writeable one in ExtEnv, it do something to ExtEnv"""

    def wrapper(self: ExtEnv, *args, **kwargs):
        api_name = str(func)  # TODO
        self.write_api_registry[api_name] = func
        return func(self, *args, **kwargs)

    return wrapper


class ExtEnv(BaseModel):
    """External Env to intergate actual game environment"""

    write_api_registry: WriteAPIRegistry = Field(default_factory=WriteAPIRegistry, include=False)
    read_api_registry: ReadAPIRegistry = Field(default_factory=ReadAPIRegistry, include=False)


class Env(ExtEnv):
    """Env to intergate with MetaGPT"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def observe(self, env_action: Union[str, EnvAPIAbstract]):
        api_name = env_action.api_name if isinstance(env_action, EnvAPIAbstract) else env_action
        read_api = self.read_api_registry.get(api_name)
        res = read_api(*env_action.args, **env_action.kwargs)
        return res

    def step(self, env_action: Union[str, Message, EnvAPIAbstract, list[EnvAPIAbstract]]):
        res = None
        if isinstance(env_action, Message):
            self.publish_message(env_action)
        elif isinstance(env_action, EnvAPIAbstract):
            write_api = self.write_api_registry.get(env_action.api_name)
            res = write_api(*env_action.args, **env_action.kwargs)

        return res

    def publish_message(self, message: "Message"):
        pass
