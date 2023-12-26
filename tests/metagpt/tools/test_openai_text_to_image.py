#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/26
@Author  : mashenquan
@File    : test_openai_text_to_image.py
"""

import pytest

from metagpt.config import CONFIG
from metagpt.tools.openai_text_to_image import oas3_openai_text_to_image


@pytest.mark.asyncio
async def test_draw():
    # Prerequisites
    assert CONFIG.OPENAI_API_KEY and CONFIG.OPENAI_API_KEY != "YOUR_API_KEY"
    assert not CONFIG.OPENAI_API_TYPE
    assert CONFIG.OPENAI_API_MODEL

    binary_data = await oas3_openai_text_to_image("Panda emoji")
    assert binary_data


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
