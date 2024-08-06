#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of ExtEnv&Env

from typing import Any, Optional

import pytest

from metagpt.environment.api.env_api import EnvAPIAbstract
from metagpt.environment.base_env import (
    Environment,
    env_read_api_registry,
    env_write_api_registry,
    mark_as_readable,
    mark_as_writeable,
)
from metagpt.environment.base_env_space import BaseEnvAction, BaseEnvObsParams


class ForTestEnv(Environment):
    value: int = 0

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        pass

    def observe(self, obs_params: Optional[BaseEnvObsParams] = None) -> Any:
        pass

    def step(self, action: BaseEnvAction) -> tuple[dict[str, Any], float, bool, bool, dict[str, Any]]:
        pass

    @mark_as_readable
    def read_api_no_param(self):
        return self.value

    @mark_as_readable
    def read_api(self, a: int, b: int):
        return a + b

    @mark_as_writeable
    def write_api(self, a: int, b: int):
        self.value = a + b

    @mark_as_writeable
    async def async_read_api(self, a: int, b: int):
        return a + b


@pytest.mark.asyncio
async def test_ext_env():
    env = ForTestEnv()
    assert len(env_read_api_registry) > 0
    assert len(env_write_api_registry) > 0

    apis = env.get_all_available_apis(mode="read")
    assert len(apis) > 0
    assert len(apis["read_api"]) == 3

    _ = await env.write_thru_api(EnvAPIAbstract(api_name="write_api", kwargs={"a": 5, "b": 10}))
    assert env.value == 15

    with pytest.raises(KeyError):
        await env.read_from_api("not_exist_api")

    assert await env.read_from_api("read_api_no_param") == 15
    assert await env.read_from_api(EnvAPIAbstract(api_name="read_api", kwargs={"a": 5, "b": 5})) == 10
