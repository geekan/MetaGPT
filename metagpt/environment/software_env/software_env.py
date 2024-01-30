#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : MG Software Env

from pydantic import ConfigDict, Field, SerializeAsAny

from metagpt.environment.base_env import Env


class SoftwareEnv(Env):
    """环境，承载一批角色，角色可以向环境发布消息，可以被其他角色观察到
    Environment, hosting a batch of roles, roles can publish messages to the environment, and can be observed by other roles
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    desc: str = Field(default="")  # 环境描述
    roles: dict[str, SerializeAsAny[Role]] = Field(default_factory=dict, validate_default=True)
    member_addrs: dict[Role, Set] = Field(default_factory=dict, exclude=True)
    history: str = ""  # For debug
    context: Context = Field(default_factory=Context, exclude=True)
