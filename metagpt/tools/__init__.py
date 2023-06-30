#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/29 15:35
@Author  : alexanderwu
@File    : __init__.py
"""


from enum import Enum, auto


class SearchEngineType(Enum):
    SERPAPI_GOOGLE = auto()
    DIRECT_GOOGLE = auto()
    CUSTOM_ENGINE = auto()
