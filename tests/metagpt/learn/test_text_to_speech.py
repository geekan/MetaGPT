#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18
@Author  : mashenquan
@File    : test_text_to_speech.py
@Desc    : Unit tests.
"""
import uuid

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
    mock_data.get.return_value = b"mock_result"

    mocker.patch.object(SpeechSynthesizer, "speak_ssml_async", return_value=mock_data)
    mocker.patch.object(S3, "cache", return_value="http://mock.s3.com/1.wav")

    # Prerequisites
    config.iflytek_app_id = ""
    config.iflytek_api_key = ""
    config.iflytek_api_secret = ""
    config.azure_tts_subscription_key = uuid.uuid4().hex
    config.azure_tts_region = "us_east"

    # test azure
    data = await text_to_speech("panda emoji", config=config)
    print(data)
    # assert "base64" in data or "http" in data


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
    config.iflytek_app_id = uuid.uuid4().hex
    config.iflytek_api_key = uuid.uuid4().hex
    config.iflytek_api_secret = uuid.uuid4().hex
    config.azure_tts_subscription_key = ""
    config.azure_tts_region = ""

    # test azure
    data = await text_to_speech("panda emoji", config=config)
    assert "base64" in data or "http" in data


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
