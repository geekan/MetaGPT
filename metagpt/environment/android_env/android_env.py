#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : MG Android Env

from pydantic import Field

from metagpt.environment.android_env.android_ext_env import AndroidExtEnv
from metagpt.environment.base_env import Environment


class AndroidEnv(Environment, AndroidExtEnv):
    rows: int = Field(default=0, description="rows of a grid on the screenshot")
    cols: int = Field(default=0, description="cols of a grid on the screenshot")
