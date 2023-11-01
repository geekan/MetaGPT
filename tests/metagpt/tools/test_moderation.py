#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/26 14:46
@Author  : zhanglei
@File    : test_moderation.py
"""

import pytest

from metagpt.tools.moderation import Moderation


@pytest.mark.parametrize(
    ("content",),
    [
        [
            ["I will kill you", "The weather is really nice today", "I want to hit you"],
        ]
    ],
)
def test_moderation(content):
    moderation = Moderation()
    results = moderation.moderation(content=content)
    assert isinstance(results, list)
    assert len(results) == len(content)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("content",),
    [
        [
            ["I will kill you", "The weather is really nice today", "I want to hit you"],
        ]
    ],
)
async def test_amoderation(content):
    moderation = Moderation()
    results = await moderation.amoderation(content=content)
    assert isinstance(results, list)
    assert len(results) == len(content)
