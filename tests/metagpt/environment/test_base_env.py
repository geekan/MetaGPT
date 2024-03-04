#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of ExtEnv&Env

import pytest

from metagpt.environment.api.env_api import EnvAPIAbstract
from metagpt.environment.base_env import Env, mark_as_readable, mark_as_writeable


class ForTestEnv(Env):
    value: int = 0

    @mark_as_readable
    def read_api_no_parms(self):
        return self.value

    @mark_as_readable
    def read_api(self, a: int, b: int):
        return a + b

    @mark_as_writeable
    def write_api(self, a: int, b: int):
        self.value = a + b


def test_ext_env():
    env = ForTestEnv()
    assert len(env.read_api_registry) == 2
    assert len(env.write_api_registry) == 1

    assert env.step(EnvAPIAbstract(api_name="write_api", kwargs={"a": 5, "b": 10})) == 15
    with pytest.raises(ValueError):
        env.observe("not_exist_api")

    assert env.observe("read_api_no_parms") == 15
    assert env.observe(EnvAPIAbstract(api_name="read_api", kwargs={"a": 5, "b": 5})) == 10
