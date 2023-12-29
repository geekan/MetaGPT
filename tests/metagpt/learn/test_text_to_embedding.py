#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18
@Author  : mashenquan
@File    : test_text_to_embedding.py
@Desc    : Unit tests.
"""

import pytest

from metagpt.config import CONFIG
from metagpt.learn.text_to_embedding import text_to_embedding


@pytest.mark.asyncio
async def test_text_to_embedding():
    # Prerequisites
    assert CONFIG.OPENAI_API_KEY

    v = await text_to_embedding(text="Panda emoji")
    assert len(v.data) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
