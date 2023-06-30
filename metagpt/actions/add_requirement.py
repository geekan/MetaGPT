#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/20 17:46
@Author  : alexanderwu
@File    : add_requirement.py
"""
from metagpt.actions import Action


class BossRequirement(Action):
    """Boss Requirement without any implementation details"""
    async def run(self, *args, **kwargs):
        raise NotImplementedError
