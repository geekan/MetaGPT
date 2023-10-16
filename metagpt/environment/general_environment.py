#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

from typing import Callable

from pydantic import Field

from metagpt.environment.environment import Environment


class GeneralEnvironment(Environment):
    """
    A GeneralEnvironment for interfacing with games, etc. It create a registration mechanism to register
    custom methods when operating with the particular environment.
    """
    name: str = Field(default="")
    registered_funcs: dict[str, Callable] = Field(default={})

    def register_func(self, func_name: str, func: Callable):
        if func_name not in self.registered_funcs:
            self.registered_funcs[func_name] = func

    def call_func(self, func_name: str, *args, **kwargs):
        assert func_name in self.registered_funcs

        func = self.registered_funcs.get(func_name)
        return func(*args, **kwargs)

    @staticmethod
    def init_register_funcs(self):
        raise NotImplementedError()
