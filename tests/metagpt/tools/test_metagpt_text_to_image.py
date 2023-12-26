#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/26
@Author  : mashenquan
@File    : test_metagpt_text_to_image.py
"""

import pytest

from metagpt.config import CONFIG
from metagpt.tools.metagpt_text_to_image import oas3_metagpt_text_to_image


@pytest.mark.asyncio
async def test_draw():
    # Prerequisites
    assert CONFIG.METAGPT_TEXT_TO_IMAGE_MODEL_URL

    binary_data = await oas3_metagpt_text_to_image("Panda emoji")
    assert binary_data


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
