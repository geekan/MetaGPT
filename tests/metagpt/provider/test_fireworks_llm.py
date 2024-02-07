#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of fireworks api

import pytest
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.completion_usage import CompletionUsage

from metagpt.provider.fireworks_api import (
    MODEL_GRADE_TOKEN_COSTS,
    FireworksCostManager,
    FireworksLLM,
)
from metagpt.utils.cost_manager import Costs
from tests.metagpt.provider.mock_llm_config import mock_llm_config
from tests.metagpt.provider.req_resp_const import (
    get_openai_chat_completion,
    get_openai_chat_completion_chunk,
    messages,
    prompt,
    resp_cont_tmpl,
)

name = "fireworks"
resp_cont = resp_cont_tmpl.format(name=name)
default_resp = get_openai_chat_completion(name)
default_resp_chunk = get_openai_chat_completion_chunk(name, usage_as_dict=True)


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

    fireworks_llm = FireworksLLM(mock_llm_config)
    fireworks_llm.model = "llama-v2-13b-chat"

    fireworks_llm._update_costs(
        usage=CompletionUsage(prompt_tokens=500000, completion_tokens=500000, total_tokens=1000000)
    )
    assert fireworks_llm.get_costs() == Costs(
        total_prompt_tokens=500000, total_completion_tokens=500000, total_cost=0.5, total_budget=0
    )

    resp = await fireworks_llm.acompletion(messages)
    assert resp.choices[0].message.content in resp_cont

    resp = await fireworks_llm.aask(prompt, stream=False)
    assert resp == resp_cont

    resp = await fireworks_llm.acompletion_text(messages, stream=False)
    assert resp == resp_cont

    resp = await fireworks_llm.acompletion_text(messages, stream=True)
    assert resp == resp_cont

    resp = await fireworks_llm.aask(prompt)
    assert resp == resp_cont
