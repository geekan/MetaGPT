#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/26 14:46
@Author  : zhanglei
@File    : test_moderation.py
"""

import pytest

from metagpt.config2 import config
from metagpt.llm import LLM
from metagpt.tools.moderation import Moderation


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
    # Prerequisites
    assert config.get_openai_llm()

    moderation = Moderation(LLM())
    results = await moderation.amoderation(content=content)
    assert isinstance(results, list)
    assert len(results) == len(content)

    results = await moderation.amoderation_with_categories(content=content)
    assert isinstance(results, list)
    assert results
    for m in results:
        assert "flagged" in m
        assert "true_categories" in m


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
