#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :  the environment api store

from typing import Callable

from pydantic import BaseModel, Field


class EnvAPIAbstract(BaseModel):
    """api/interface summary description"""

    api_name: str = Field(default="", description="the api function name or id")
    args: set = Field(default={}, description="the api function `args` params")
    kwargs: dict = Field(default=dict(), description="the api function `kwargs` params")


class EnvAPIRegistry(BaseModel):
    """the registry to store environment w&r api/interface"""

    registry: dict[str, Callable] = Field(default=dict(), include=False)

    def get(self, api_name: str):
        return self.registry.get(api_name)


class WriteAPIRegistry(EnvAPIRegistry):
    """just as a new class name"""

    pass


class ReadAPIRegistry(EnvAPIRegistry):
    """just as a new class name"""

    pass
