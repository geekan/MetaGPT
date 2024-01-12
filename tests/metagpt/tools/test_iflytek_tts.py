#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/26
@Author  : mashenquan
@File    : test_iflytek_tts.py
"""
import pytest

from metagpt.config2 import Config
from metagpt.tools.iflytek_tts import IFlyTekTTS, oas3_iflytek_tts


@pytest.mark.asyncio
async def test_iflytek_tts(mocker):
    # mock
    config = Config.default()
    config.AZURE_TTS_SUBSCRIPTION_KEY = None
    config.AZURE_TTS_REGION = None
    mocker.patch.object(IFlyTekTTS, "synthesize_speech", return_value=None)
    mock_data = mocker.AsyncMock()
    mock_data.read.return_value = b"mock iflytek"
    mock_reader = mocker.patch("aiofiles.open")
    mock_reader.return_value.__aenter__.return_value = mock_data

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
