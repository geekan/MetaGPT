#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/26
@Author  : mashenquan
@File    : test_openai_text_to_image.py
"""

import pytest

from metagpt.config import CONFIG
from metagpt.tools.openai_text_to_image import (
    OpenAIText2Image,
    oas3_openai_text_to_image,
)


@pytest.mark.asyncio
async def test_draw():
    # Prerequisites
    assert CONFIG.OPENAI_API_KEY and CONFIG.OPENAI_API_KEY != "YOUR_API_KEY"
    assert not CONFIG.OPENAI_API_TYPE
    assert CONFIG.OPENAI_API_MODEL

    binary_data = await oas3_openai_text_to_image("Panda emoji")
    assert binary_data


@pytest.mark.asyncio
async def test_get_image():
    data = await OpenAIText2Image.get_image_data(
        url="https://www.baidu.com/img/PCtm_d9c8750bed0b3c7d089fa7d55720d6cf.png"
    )
    assert data


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
