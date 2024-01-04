#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of ollama api

import pytest

from metagpt.provider.ollama_api import OllamaGPTAPI

messages = [{"role": "user", "content": "who are you"}]


default_resp = {"message": {"role": "assisant", "content": "I'm ollama"}}


def mock_llm_ask(self, messages: list[dict]) -> dict:
    return default_resp


def test_gemini_completion(mocker):
    mocker.patch("metagpt.provider.ollama_api.OllamaGPTAPI.completion", mock_llm_ask)
    resp = OllamaGPTAPI().completion(messages)
    assert resp["message"]["content"] == default_resp["message"]["content"]


async def mock_llm_aask(self, messgaes: list[dict]) -> dict:
    return default_resp


@pytest.mark.asyncio
async def test_gemini_acompletion(mocker):
    mocker.patch("metagpt.provider.ollama_api.OllamaGPTAPI.acompletion", mock_llm_aask)
    resp = await OllamaGPTAPI().acompletion(messages)
    assert resp["message"]["content"] == default_resp["message"]["content"]
