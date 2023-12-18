#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/18
@Author  : mashenquan
@File    : role_run.py
@Desc    : Message type caused by `Role.run()` invocation.
"""
from metagpt.actions import Action


class RoleRun(Action):
    """Message type caused by `Role.run` invocation"""

    async def run(self, *args, **kwargs):
        raise NotImplementedError
