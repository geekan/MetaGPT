#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18
@Author  : mashenquan
@File    : test_text_to_image.py
@Desc    : Unit tests.
"""


import pytest

from metagpt.config import CONFIG
from metagpt.learn.text_to_image import text_to_image


@pytest.mark.asyncio
async def test():
    # Prerequisites
    assert CONFIG.METAGPT_TEXT_TO_IMAGE_MODEL_URL
    assert CONFIG.OPENAI_API_KEY

    data = await text_to_image("Panda emoji", size_type="512x512")
    assert "base64" in data or "http" in data
    key = CONFIG.METAGPT_TEXT_TO_IMAGE_MODEL_URL
    CONFIG.METAGPT_TEXT_TO_IMAGE_MODEL_URL = None
    try:
        data = await text_to_image("Panda emoji", size_type="512x512")
        assert "base64" in data or "http" in data
    finally:
        CONFIG.METAGPT_TEXT_TO_IMAGE_MODEL_URL = key


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
