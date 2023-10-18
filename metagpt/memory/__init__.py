#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/30 20:57
@Author  : alexanderwu
@File    : __init__.py
"""

from metagpt.memory.longterm_memory import LongTermMemory
from metagpt.memory.memory import Memory

__all__ = [
    "Memory",
    "LongTermMemory",
]
