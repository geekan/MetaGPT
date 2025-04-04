#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/29 15:35
@Author  : alexanderwu
@File    : __init__.py
"""

from metagpt.core.configs.browser_config import WebBrowserEngineType
from metagpt.core.configs.search_config import SearchEngineType
from metagpt.core.tools import TOOL_REGISTRY
from metagpt.tools import libs  # this registers all tools

_ = libs, TOOL_REGISTRY  # Avoid pre-commit error


class SearchInterface:
    async def asearch(self, *args, **kwargs):
        ...


__all__ = ["SearchEngineType", "WebBrowserEngineType"]
