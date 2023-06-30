#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/23 17:25
@Author  : alexanderwu
@File    : seacher.py
"""
from metagpt.roles import Role
from metagpt.actions import SearchAndSummarize
from metagpt.tools import SearchEngineType


class Searcher(Role):
    def __init__(self, name='Alice', profile='Smart Assistant', goal='Provide search services for users',
                 constraints='Answer is rich and complete', **kwargs):
        super().__init__(name, profile, goal, constraints, **kwargs)
        self._init_actions([SearchAndSummarize])

    def set_search_func(self, search_func):
        action = SearchAndSummarize("", engine=SearchEngineType.CUSTOM_ENGINE, search_func=search_func)
        self._init_actions([action])
