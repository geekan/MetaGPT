#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/26
@Author  : mashenquan
@File    : test_iflytek_tts.py
"""
import pytest

from metagpt.config import CONFIG
from metagpt.tools.iflytek_tts import oas3_iflytek_tts


@pytest.mark.asyncio
async def test_tts():
    # Prerequisites
    assert CONFIG.IFLYTEK_APP_ID
    assert CONFIG.IFLYTEK_API_KEY
    assert CONFIG.IFLYTEK_API_SECRET

    result = await oas3_iflytek_tts(
        text="你好，hello",
        app_id=CONFIG.IFLYTEK_APP_ID,
        api_key=CONFIG.IFLYTEK_API_KEY,
        api_secret=CONFIG.IFLYTEK_API_SECRET,
    )
    assert result


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
