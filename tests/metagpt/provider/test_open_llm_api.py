#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

import pytest
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.completion_usage import CompletionUsage

from metagpt.provider.open_llm_api import OpenLLM
from metagpt.utils.cost_manager import CostManager, Costs
from tests.metagpt.provider.mock_llm_config import mock_llm_config
from tests.metagpt.provider.req_resp_const import (
    get_openai_chat_completion,
    get_openai_chat_completion_chunk,
    messages,
    prompt,
    resp_cont_tmpl,
)

llm_name = "llama2-7b"
resp_cont = resp_cont_tmpl.format(name=llm_name)
default_resp = get_openai_chat_completion(llm_name)

default_resp_chunk = get_openai_chat_completion_chunk(llm_name)


async def mock_openai_acompletions_create(self, stream: bool = False, **kwargs) -> ChatCompletionChunk:
    if stream:

        class Iterator(object):
            async def __aiter__(self):
                yield default_resp_chunk

        return Iterator()
    else:
        return default_resp


@pytest.mark.asyncio
async def test_openllm_acompletion(mocker):
    mocker.patch("openai.resources.chat.completions.AsyncCompletions.create", mock_openai_acompletions_create)

    openllm_gpt = OpenLLM(mock_llm_config)
    openllm_gpt.model = "llama-v2-13b-chat"

    openllm_gpt.cost_manager = CostManager()
    openllm_gpt._update_costs(usage=CompletionUsage(prompt_tokens=100, completion_tokens=100, total_tokens=200))
    assert openllm_gpt.get_costs() == Costs(
        total_prompt_tokens=100, total_completion_tokens=100, total_cost=0, total_budget=0
    )

    resp = await openllm_gpt.acompletion(messages)
    assert resp.choices[0].message.content in resp_cont

    resp = await openllm_gpt.aask(prompt, stream=False)
    assert resp == resp_cont

    resp = await openllm_gpt.acompletion_text(messages, stream=False)
    assert resp == resp_cont

    resp = await openllm_gpt.acompletion_text(messages, stream=True)
    assert resp == resp_cont

    resp = await openllm_gpt.aask(prompt)
    assert resp == resp_cont
