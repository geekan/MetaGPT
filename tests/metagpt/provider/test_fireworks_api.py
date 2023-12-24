#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of fireworks api

import pytest
from openai.types.chat.chat_completion import (
    ChatCompletion,
    ChatCompletionMessage,
    Choice,
)
from openai.types.completion_usage import CompletionUsage

from metagpt.provider.fireworks_api import FireWorksGPTAPI

default_resp = ChatCompletion(
    id="cmpl-a6652c1bb181caae8dd19ad8",
    model="accounts/fireworks/models/llama-v2-13b-chat",
    object="chat.completion",
    created=1703300855,
    choices=[
        Choice(finish_reason="stop", index=0, message=ChatCompletionMessage(role="assistant", content="I'm fireworks"))
    ],
    usage=CompletionUsage(completion_tokens=110, prompt_tokens=92, total_tokens=202),
)

messages = [{"role": "user", "content": "who are you"}]


def mock_llm_ask(self, messages: list[dict]) -> ChatCompletion:
    return default_resp


def test_fireworks_completion(mocker):
    mocker.patch("metagpt.provider.fireworks_api.FireWorksGPTAPI.completion", mock_llm_ask)

    resp = FireWorksGPTAPI().completion(messages)
    assert "fireworks" in resp.choices[0].message.content


async def mock_llm_aask(self, messgaes: list[dict], stream: bool = False) -> ChatCompletion:
    return default_resp


@pytest.mark.asyncio
async def test_fireworks_acompletion(mocker):
    mocker.patch("metagpt.provider.fireworks_api.FireWorksGPTAPI.acompletion", mock_llm_aask)

    resp = await FireWorksGPTAPI().acompletion(messages, stream=False)

    assert "fireworks" in resp.choices[0].message.content
