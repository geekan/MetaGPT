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
    SERPER_GOOGLE = auto()
    DUCK_DUCK_GO = auto()
    CUSTOM_ENGINE = auto()


class WebBrowserEngineType(Enum):
    PLAYWRIGHT = "playwright"
    SELENIUM = "selenium"
    CUSTOM = "custom"
