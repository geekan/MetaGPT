#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of google gemini api

import pytest
from abc import ABC
from dataclasses import dataclass

from metagpt.provider.google_gemini_api import GeminiGPTAPI


messages = [
    {"role": "user", "content": "who are you"}
]


@dataclass
class MockGeminiResponse(ABC):
    text: str


default_resp = MockGeminiResponse(text="I'm gemini from google")


def mock_llm_ask(self, messages: list[dict]) -> MockGeminiResponse:
    return default_resp


def test_gemini_completion(mocker):
    mocker.patch("metagpt.provider.google_gemini_api.GeminiGPTAPI.completion", mock_llm_ask)
    resp = GeminiGPTAPI().completion(messages)
    assert resp.text == default_resp.text


async def mock_llm_aask(self, messgaes: list[dict]) -> MockGeminiResponse:
    return default_resp


@pytest.mark.asyncio
async def test_gemini_acompletion(mocker):
    mocker.patch("metagpt.provider.google_gemini_api.GeminiGPTAPI.acompletion", mock_llm_aask)
    resp = await GeminiGPTAPI().acompletion(messages)
    assert resp.text == default_resp.text
