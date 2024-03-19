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
    config.azure_tts_subscription_key = None
    config.azure_tts_region = None
    mocker.patch.object(IFlyTekTTS, "synthesize_speech", return_value=None)
    mock_data = mocker.AsyncMock()
    mock_data.read.return_value = b"mock iflytek"
    mock_reader = mocker.patch("aiofiles.open")
    mock_reader.return_value.__aenter__.return_value = mock_data

    # Prerequisites
    assert config.iflytek_app_id
    assert config.iflytek_api_key
    assert config.iflytek_api_secret

    result = await oas3_iflytek_tts(
        text="你好，hello",
        app_id=config.iflytek_app_id,
        api_key=config.iflytek_api_key,
        api_secret=config.iflytek_api_secret,
    )
    assert result


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
