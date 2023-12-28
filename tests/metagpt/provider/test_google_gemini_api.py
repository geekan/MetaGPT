#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of google gemini api

from abc import ABC
from dataclasses import dataclass

import pytest
from google.ai import generativelanguage as glm
from google.generativeai.types import content_types

from metagpt.config import CONFIG
from metagpt.provider.google_gemini_api import GeminiLLM

CONFIG.gemini_api_key = "xx"


@dataclass
class MockGeminiResponse(ABC):
    text: str


prompt_msg = "who are you"
messages = [{"role": "user", "parts": prompt_msg}]
resp_content = "I'm gemini from google"
default_resp = MockGeminiResponse(text=resp_content)


def mock_gemini_count_tokens(self, contents: content_types.ContentsType) -> glm.CountTokensResponse:
    return glm.CountTokensResponse(total_tokens=20)


async def mock_gemini_count_tokens_async(self, contents: content_types.ContentsType) -> glm.CountTokensResponse:
    return glm.CountTokensResponse(total_tokens=20)


def mock_gemini_generate_content(self, **kwargs) -> MockGeminiResponse:
    return default_resp


async def mock_gemini_generate_content_async(self, stream: bool = False, **kwargs) -> MockGeminiResponse:
    if stream:

        class Iterator(object):
            async def __aiter__(self):
                yield default_resp

        return Iterator()
    else:
        return default_resp


@pytest.mark.asyncio
async def test_gemini_acompletion(mocker):
    mocker.patch("metagpt.provider.google_gemini_api.GeminiGenerativeModel.count_tokens", mock_gemini_count_tokens)
    mocker.patch(
        "metagpt.provider.google_gemini_api.GeminiGenerativeModel.count_tokens_async", mock_gemini_count_tokens_async
    )
    mocker.patch("google.generativeai.generative_models.GenerativeModel.generate_content", mock_gemini_generate_content)
    mocker.patch(
        "google.generativeai.generative_models.GenerativeModel.generate_content_async",
        mock_gemini_generate_content_async,
    )

    gemini_gpt = GeminiLLM()

    assert gemini_gpt._user_msg(prompt_msg) == {"role": "user", "parts": [prompt_msg]}
    assert gemini_gpt._assistant_msg(prompt_msg) == {"role": "model", "parts": [prompt_msg]}

    usage = gemini_gpt.get_usage(messages, resp_content)
    assert usage == {"prompt_tokens": 20, "completion_tokens": 20}

    resp = gemini_gpt.completion(messages)
    assert resp == default_resp

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
