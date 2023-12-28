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

from metagpt.provider.fireworks_api import (
    MODEL_GRADE_TOKEN_COSTS,
    FireworksCostManager,
    FireworksLLM,
)

resp_content = "I'm fireworks"
default_resp = ChatCompletion(
    id="cmpl-a6652c1bb181caae8dd19ad8",
    model="accounts/fireworks/models/llama-v2-13b-chat",
    object="chat.completion",
    created=1703300855,
    choices=[
        Choice(finish_reason="stop", index=0, message=ChatCompletionMessage(role="assistant", content=resp_content))
    ],
    usage=CompletionUsage(completion_tokens=110, prompt_tokens=92, total_tokens=202),
)

prompt_msg = "who are you"
messages = [{"role": "user", "content": prompt_msg}]


def test_fireworks_costmanager():
    cost_manager = FireworksCostManager()
    assert MODEL_GRADE_TOKEN_COSTS["-1"] == cost_manager.model_grade_token_costs("test")
    assert MODEL_GRADE_TOKEN_COSTS["-1"] == cost_manager.model_grade_token_costs("xxx-81b-chat")
    assert MODEL_GRADE_TOKEN_COSTS["16"] == cost_manager.model_grade_token_costs("llama-v2-13b-chat")
    assert MODEL_GRADE_TOKEN_COSTS["16"] == cost_manager.model_grade_token_costs("xxx-15.5b-chat")
    assert MODEL_GRADE_TOKEN_COSTS["16"] == cost_manager.model_grade_token_costs("xxx-16b-chat")
    assert MODEL_GRADE_TOKEN_COSTS["80"] == cost_manager.model_grade_token_costs("xxx-80b-chat")
    assert MODEL_GRADE_TOKEN_COSTS["mixtral-8x7b"] == cost_manager.model_grade_token_costs("mixtral-8x7b-chat")


def mock_llm_completion(self, messages: list[dict], timeout: int = 60) -> ChatCompletion:
    return default_resp


async def mock_llm_acompletion(self, messgaes: list[dict], stream: bool = False, timeout: int = 60) -> ChatCompletion:
    return default_resp


async def mock_llm_achat_completion_stream(self, messgaes: list[dict]) -> str:
    return default_resp.choices[0].message.content


@pytest.mark.asyncio
async def test_fireworks_acompletion(mocker):
    mocker.patch("metagpt.provider.fireworks_api.FireworksLLM.acompletion", mock_llm_acompletion)
    mocker.patch("metagpt.provider.fireworks_api.FireworksLLM._achat_completion", mock_llm_acompletion)
    mocker.patch(
        "metagpt.provider.fireworks_api.FireworksLLM._achat_completion_stream", mock_llm_achat_completion_stream
    )
    fireworks_gpt = FireworksLLM()

    resp = await fireworks_gpt.acompletion(messages, stream=False)
    assert resp.choices[0].message.content in resp_content

    resp = await fireworks_gpt.aask(prompt_msg, stream=False)
    assert resp == resp_content

    resp = await fireworks_gpt.acompletion_text(messages, stream=False)
    assert resp == resp_content

    resp = await fireworks_gpt.acompletion_text(messages, stream=True)
    assert resp == resp_content

    resp = await fireworks_gpt.aask(prompt_msg)
    assert resp == resp_content
