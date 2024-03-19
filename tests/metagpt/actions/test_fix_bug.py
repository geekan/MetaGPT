#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/25 22:38
@Author  : alexanderwu
@File    : test_fix_bug.py
"""

import pytest

from metagpt.actions.fix_bug import FixBug


@pytest.mark.asyncio
async def test_fix_bug(context):
    fix_bug = FixBug(context=context)
    assert fix_bug.name == "FixBug"
