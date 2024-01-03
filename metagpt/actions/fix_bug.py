# -*- coding: utf-8 -*-
"""
@Time    : 2023-12-12
@Author  : mashenquan
@File    : fix_bug.py
"""
from metagpt.actions import Action


class FixBug(Action):
    """Fix bug action without any implementation details"""

    name: str = "FixBug"
