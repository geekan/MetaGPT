#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of google gemini api

from abc import ABC
from dataclasses import dataclass

import pytest
from google.ai import generativelanguage as glm
from google.generativeai.types import content_types

from metagpt.provider.google_gemini_api import GeminiLLM
from tests.metagpt.provider.mock_llm_config import mock_llm_config
from tests.metagpt.provider.req_resp_const import (
    gemini_messages,
    llm_general_chat_funcs_test,
    prompt,
    resp_cont_tmpl,
)


@dataclass
class MockGeminiResponse(ABC):
    text: str


resp_cont = resp_cont_tmpl.format(name="gemini")
default_resp = MockGeminiResponse(text=resp_cont)


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

    gemini_llm = GeminiLLM(mock_llm_config)

    assert gemini_llm._user_msg(prompt) == {"role": "user", "parts": [prompt]}
    assert gemini_llm._assistant_msg(prompt) == {"role": "model", "parts": [prompt]}

    usage = gemini_llm.get_usage(gemini_messages, resp_cont)
    assert usage == {"prompt_tokens": 20, "completion_tokens": 20}

    resp = gemini_llm.completion(gemini_messages)
    assert resp == default_resp

    resp = await gemini_llm.acompletion(gemini_messages)
    assert resp.text == default_resp.text

    await llm_general_chat_funcs_test(gemini_llm, prompt, gemini_messages, resp_cont)
