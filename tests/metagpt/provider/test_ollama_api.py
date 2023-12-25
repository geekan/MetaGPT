#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of ollama api

import pytest

from metagpt.config import CONFIG
from metagpt.provider.ollama_api import OllamaGPTAPI

prompt_msg = "who are you"
messages = [{"role": "user", "content": prompt_msg}]

resp_content = "I'm ollama"
default_resp = {"message": {"role": "assistant", "content": resp_content}}

CONFIG.ollama_api_base = "http://xxx"


def mock_llm_completion(self, messages: list[dict], timeout: int = 60) -> dict:
    return default_resp


async def mock_llm_acompletion(self, messgaes: list[dict], stream: bool = False, timeout: int = 60) -> dict:
    return default_resp


async def mock_llm_achat_completion_stream(self, messgaes: list[dict]) -> str:
    return resp_content


def test_gemini_completion(mocker):
    mocker.patch("metagpt.provider.ollama_api.OllamaGPTAPI.completion", mock_llm_completion)
    ollama_gpt = OllamaGPTAPI()
    resp = ollama_gpt.completion(messages)
    assert resp["message"]["content"] == default_resp["message"]["content"]

    resp = ollama_gpt.ask(prompt_msg)
    assert resp == resp_content


@pytest.mark.asyncio
async def test_gemini_acompletion(mocker):
    mocker.patch("metagpt.provider.ollama_api.OllamaGPTAPI.acompletion", mock_llm_acompletion)
    mocker.patch("metagpt.provider.ollama_api.OllamaGPTAPI._achat_completion", mock_llm_acompletion)
    mocker.patch("metagpt.provider.ollama_api.OllamaGPTAPI._achat_completion_stream", mock_llm_achat_completion_stream)
    ollama_gpt = OllamaGPTAPI()

    resp = await ollama_gpt.acompletion(messages)
    assert resp["message"]["content"] == default_resp["message"]["content"]

    resp = await ollama_gpt.aask(prompt_msg, stream=False)
    assert resp == resp_content

    resp = await ollama_gpt.acompletion_text(messages, stream=False)
    assert resp == resp_content

    resp = await ollama_gpt.acompletion_text(messages, stream=True)
    assert resp == resp_content

    resp = await ollama_gpt.aask(prompt_msg)
    assert resp == resp_content
