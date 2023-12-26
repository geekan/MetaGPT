#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of google gemini api

from abc import ABC
from dataclasses import dataclass

import pytest

from metagpt.provider.google_gemini_api import GeminiGPTAPI


@dataclass
class MockGeminiResponse(ABC):
    text: str


prompt_msg = "who are you"
messages = [{"role": "user", "parts": prompt_msg}]
resp_content = "I'm gemini from google"
default_resp = MockGeminiResponse(text=resp_content)


def mock_llm_completion(self, messages: list[dict], timeout: int = 60) -> MockGeminiResponse:
    return default_resp


async def mock_llm_acompletion(
    self, messgaes: list[dict], stream: bool = False, timeout: int = 60
) -> MockGeminiResponse:
    return default_resp


async def mock_llm_achat_completion_stream(self, messgaes: list[dict]) -> str:
    return resp_content


@pytest.mark.asyncio
async def test_gemini_acompletion(mocker):
    mocker.patch("metagpt.provider.google_gemini_api.GeminiGPTAPI.acompletion", mock_llm_acompletion)
    mocker.patch("metagpt.provider.google_gemini_api.GeminiGPTAPI._achat_completion", mock_llm_acompletion)
    mocker.patch(
        "metagpt.provider.google_gemini_api.GeminiGPTAPI._achat_completion_stream", mock_llm_achat_completion_stream
    )
    gemini_gpt = GeminiGPTAPI()

    resp = await gemini_gpt.acompletion(messages)
    assert resp.text == default_resp.text

    resp = await gemini_gpt.aask(prompt_msg, stream=False)
    assert resp == resp_content

    resp = await gemini_gpt.acompletion_text(messages, stream=False)
    assert resp == resp_content

    resp = await gemini_gpt.acompletion_text(messages, stream=True)
    assert resp == resp_content

    resp = await gemini_gpt.aask(prompt_msg)
    assert resp == resp_content
