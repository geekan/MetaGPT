#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/26
@Author  : mashenquan
@File    : test_iflytek_tts.py
"""
import pytest

from metagpt.config2 import config
from metagpt.tools.iflytek_tts import oas3_iflytek_tts


@pytest.mark.asyncio
async def test_tts():
    # Prerequisites
    assert config.IFLYTEK_APP_ID
    assert config.IFLYTEK_API_KEY
    assert config.IFLYTEK_API_SECRET

    result = await oas3_iflytek_tts(
        text="你好，hello",
        app_id=config.IFLYTEK_APP_ID,
        api_key=config.IFLYTEK_API_KEY,
        api_secret=config.IFLYTEK_API_SECRET,
    )
    assert result


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
