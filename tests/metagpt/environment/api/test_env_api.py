#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

from metagpt.environment.api.env_api import EnvAPIRegistry


def test_env_api_registry():
    def test_func():
        pass

    env_api_registry = EnvAPIRegistry()
    env_api_registry["test"] = test_func

    env_api_registry.get("test") == test_func
