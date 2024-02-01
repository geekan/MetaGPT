#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18
@Author  : mashenquan
@File    : test_text_to_speech.py
@Desc    : Unit tests.
"""

import pytest
from azure.cognitiveservices.speech import ResultReason, SpeechSynthesizer

from metagpt.config2 import Config
from metagpt.learn.text_to_speech import text_to_speech
from metagpt.tools.iflytek_tts import IFlyTekTTS
from metagpt.utils.s3 import S3


@pytest.mark.asyncio
async def test_azure_text_to_speech(mocker):
    # mock
    config = Config.default()
    config.iflytek_api_key = None
    config.iflytek_api_secret = None
    config.iflytek_app_id = None
    mock_result = mocker.Mock()
    mock_result.audio_data = b"mock audio data"
    mock_result.reason = ResultReason.SynthesizingAudioCompleted
    mock_data = mocker.Mock()
    mock_data.get.return_value = mock_result
    mocker.patch.object(SpeechSynthesizer, "speak_ssml_async", return_value=mock_data)
    mocker.patch.object(S3, "cache", return_value="http://mock.s3.com/1.wav")

    # Prerequisites
    assert not config.iflytek_app_id
    assert not config.iflytek_api_key
    assert not config.iflytek_api_secret
    assert config.azure_tts_subscription_key and config.azure_tts_subscription_key != "YOUR_API_KEY"
    assert config.azure_tts_region

    config.copy()
    # test azure
    data = await text_to_speech("panda emoji", config=config)
    assert "base64" in data or "http" in data


@pytest.mark.asyncio
async def test_iflytek_text_to_speech(mocker):
    # mock
    config = Config.default()
    config.azure_tts_subscription_key = None
    config.azure_tts_region = None
    mocker.patch.object(IFlyTekTTS, "synthesize_speech", return_value=None)
    mock_data = mocker.AsyncMock()
    mock_data.read.return_value = b"mock iflytek"
    mock_reader = mocker.patch("aiofiles.open")
    mock_reader.return_value.__aenter__.return_value = mock_data
    mocker.patch.object(S3, "cache", return_value="http://mock.s3.com/1.mp3")

    # Prerequisites
    assert config.iflytek_app_id
    assert config.iflytek_api_key
    assert config.iflytek_api_secret
    assert not config.azure_tts_subscription_key or config.azure_tts_subscription_key == "YOUR_API_KEY"
    assert not config.azure_tts_region

    # test azure
    data = await text_to_speech("panda emoji", config=config)
    assert "base64" in data or "http" in data


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
