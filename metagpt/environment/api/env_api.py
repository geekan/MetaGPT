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

    registry: dict[str, Callable] = Field(default=dict(), exclude=True)

    def get(self, api_name: str):
        return self.registry.get(api_name)

    def __getitem__(self, api_name: str) -> Callable:
        return self.get(api_name)

    def __setitem__(self, api_name: str, func: Callable):
        self.registry[api_name] = func

    def __len__(self):
        return len(self.registry)


class WriteAPIRegistry(EnvAPIRegistry):
    """just as a explicit class name"""

    pass


class ReadAPIRegistry(EnvAPIRegistry):
    """just as a explicit class name"""

    pass
