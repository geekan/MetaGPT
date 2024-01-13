#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/29 15:35
@Author  : alexanderwu
@File    : __init__.py
"""

from enum import Enum
from metagpt.tools import tool_types  # this registers all tool types
from metagpt.tools.functions import libs  # this registers all tools
from metagpt.tools.tool_registry import TOOL_REGISTRY

_ = tool_types  # Avoid pre-commit error
_ = libs  # Avoid pre-commit error
_ = TOOL_REGISTRY  # Avoid pre-commit error


class SearchEngineType(Enum):
    SERPAPI_GOOGLE = "serpapi"
    SERPER_GOOGLE = "serper"
    DIRECT_GOOGLE = "google"
    DUCK_DUCK_GO = "ddg"
    CUSTOM_ENGINE = "custom"


class WebBrowserEngineType(Enum):
    PLAYWRIGHT = "playwright"
    SELENIUM = "selenium"
    CUSTOM = "custom"

    @classmethod
    def __missing__(cls, key):
        """Default type conversion"""
        return cls.CUSTOM
