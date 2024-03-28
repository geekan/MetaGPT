#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :  the environment api store

from typing import Any, Callable, Union

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
        if api_name not in self.registry:
            raise KeyError(f"api_name: {api_name} not found")
        return self.registry.get(api_name)

    def __getitem__(self, api_name: str) -> Callable:
        return self.get(api_name)

    def __setitem__(self, api_name: str, func: Callable):
        self.registry[api_name] = func

    def __len__(self):
        return len(self.registry)

    def get_apis(self, as_str=True) -> dict[str, dict[str, Union[dict, Any, str]]]:
        """return func schema without func instance"""
        apis = dict()
        for func_name, func_schema in self.registry.items():
            new_func_schema = dict()
            for key, value in func_schema.items():
                if key == "func":
                    continue
                new_func_schema[key] = str(value) if as_str else value
            new_func_schema = new_func_schema
            apis[func_name] = new_func_schema
        return apis


class WriteAPIRegistry(EnvAPIRegistry):
    """just as a explicit class name"""

    pass


class ReadAPIRegistry(EnvAPIRegistry):
    """just as a explicit class name"""

    pass
