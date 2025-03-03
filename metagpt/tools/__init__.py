#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/29 15:35
@Author  : alexanderwu
@File    : __init__.py
"""

from metagpt.tools import libs  # this registers all tools
from metagpt.tools.tool_registry import TOOL_REGISTRY
from metagpt.configs.search_config import SearchEngineType
from metagpt.configs.browser_config import WebBrowserEngineType


_ = libs, TOOL_REGISTRY  # Avoid pre-commit error


class SearchInterface:
    async def asearch(self, *args, **kwargs):
        ...


__all__ = ["SearchEngineType", "WebBrowserEngineType", "TOOL_REGISTRY"]
