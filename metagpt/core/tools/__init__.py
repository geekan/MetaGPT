#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/29 15:35
@Author  : alexanderwu
@File    : __init__.py
"""

from metagpt.core.tools.tool_registry import TOOL_REGISTRY

_ = TOOL_REGISTRY  # Avoid pre-commit error


__all__ = ["TOOL_REGISTRY"]
