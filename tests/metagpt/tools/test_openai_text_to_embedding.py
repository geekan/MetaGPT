#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/26
@Author  : mashenquan
@File    : test_openai_text_to_embedding.py
"""

import pytest

from metagpt.config import CONFIG
from metagpt.tools.openai_text_to_embedding import oas3_openai_text_to_embedding


@pytest.mark.asyncio
async def test_embedding():
    # Prerequisites
    assert CONFIG.OPENAI_API_KEY and CONFIG.OPENAI_API_KEY != "YOUR_API_KEY"
    assert not CONFIG.OPENAI_API_TYPE
    assert CONFIG.OPENAI_API_MODEL

    result = await oas3_openai_text_to_embedding("Panda emoji")
    assert result
    assert result.model
    assert len(result.data) > 0
    assert len(result.data[0].embedding) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
