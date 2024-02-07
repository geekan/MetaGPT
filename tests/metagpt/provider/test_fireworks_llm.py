#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of fireworks api

import pytest
from openai.types.chat.chat_completion import (
    ChatCompletion,
    ChatCompletionMessage,
    Choice,
)
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as AChoice
from openai.types.chat.chat_completion_chunk import ChoiceDelta
from openai.types.completion_usage import CompletionUsage

from metagpt.provider.fireworks_api import (
    MODEL_GRADE_TOKEN_COSTS,
    FireworksCostManager,
    FireworksLLM,
)
from metagpt.utils.cost_manager import Costs
from tests.metagpt.provider.mock_llm_config import mock_llm_config

resp_content = "I'm fireworks"
default_resp = ChatCompletion(
    id="cmpl-a6652c1bb181caae8dd19ad8",
    model="accounts/fireworks/models/llama-v2-13b-chat",
    object="chat.completion",
    created=1703300855,
    choices=[
        Choice(
            finish_reason="stop",
            index=0,
            message=ChatCompletionMessage(role="assistant", content=resp_content),
            logprobs=None,
        )
    ],
    usage=CompletionUsage(completion_tokens=110, prompt_tokens=92, total_tokens=202),
)

default_resp_chunk = ChatCompletionChunk(
    id=default_resp.id,
    model=default_resp.model,
    object="chat.completion.chunk",
    created=default_resp.created,
    choices=[
        AChoice(
            delta=ChoiceDelta(content=resp_content, role="assistant"),
            finish_reason="stop",
            index=0,
            logprobs=None,
        )
    ],
    usage=dict(default_resp.usage),
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

    cost_manager.update_cost(prompt_tokens=500000, completion_tokens=500000, model="llama-v2-13b-chat")
    assert cost_manager.total_cost == 0.5


async def mock_openai_acompletions_create(self, stream: bool = False, **kwargs) -> ChatCompletionChunk:
    if stream:

        class Iterator(object):
            async def __aiter__(self):
                yield default_resp_chunk

        return Iterator()
    else:
        return default_resp


@pytest.mark.asyncio
async def test_fireworks_acompletion(mocker):
    mocker.patch("openai.resources.chat.completions.AsyncCompletions.create", mock_openai_acompletions_create)

    fireworks_gpt = FireworksLLM(mock_llm_config)
    fireworks_gpt.model = "llama-v2-13b-chat"

    fireworks_gpt._update_costs(
        usage=CompletionUsage(prompt_tokens=500000, completion_tokens=500000, total_tokens=1000000)
    )
    assert fireworks_gpt.get_costs() == Costs(
        total_prompt_tokens=500000, total_completion_tokens=500000, total_cost=0.5, total_budget=0
    )

    resp = await fireworks_gpt.acompletion(messages)
    assert resp.choices[0].message.content in resp_content

    resp = await fireworks_gpt.aask(prompt_msg, stream=False)
    assert resp == resp_content

    resp = await fireworks_gpt.acompletion_text(messages, stream=False)
    assert resp == resp_content

    resp = await fireworks_gpt.acompletion_text(messages, stream=True)
    assert resp == resp_content

    resp = await fireworks_gpt.aask(prompt_msg)
    assert resp == resp_content
