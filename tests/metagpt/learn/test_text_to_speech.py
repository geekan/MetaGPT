#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18
@Author  : mashenquan
@File    : test_text_to_speech.py
@Desc    : Unit tests.
"""

import pytest

from metagpt.config2 import config
from metagpt.learn.text_to_speech import text_to_speech


@pytest.mark.asyncio
async def test_text_to_speech():
    # Prerequisites
    assert config.IFLYTEK_APP_ID
    assert config.IFLYTEK_API_KEY
    assert config.IFLYTEK_API_SECRET
    assert config.AZURE_TTS_SUBSCRIPTION_KEY and config.AZURE_TTS_SUBSCRIPTION_KEY != "YOUR_API_KEY"
    assert config.AZURE_TTS_REGION

    i = config.copy()
    # test azure
    data = await text_to_speech(
        "panda emoji",
        subscription_key=i.AZURE_TTS_SUBSCRIPTION_KEY,
        region=i.AZURE_TTS_REGION,
        iflytek_api_key=i.IFLYTEK_API_KEY,
        iflytek_api_secret=i.IFLYTEK_API_SECRET,
        iflytek_app_id=i.IFLYTEK_APP_ID,
    )
    assert "base64" in data or "http" in data

    # test iflytek
    ## Mock session env
    i.AZURE_TTS_SUBSCRIPTION_KEY = ""
    data = await text_to_speech(
        "panda emoji",
        subscription_key=i.AZURE_TTS_SUBSCRIPTION_KEY,
        region=i.AZURE_TTS_REGION,
        iflytek_api_key=i.IFLYTEK_API_KEY,
        iflytek_api_secret=i.IFLYTEK_API_SECRET,
        iflytek_app_id=i.IFLYTEK_APP_ID,
    )
    assert "base64" in data or "http" in data


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
