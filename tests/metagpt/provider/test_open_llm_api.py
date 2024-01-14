#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

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

from metagpt.config import CONFIG
from metagpt.provider.open_llm_api import OpenLLM
from metagpt.utils.cost_manager import Costs

CONFIG.max_budget = 10
CONFIG.calc_usage = True

resp_content = "I'm llama2"
default_resp = ChatCompletion(
    id="cmpl-a6652c1bb181caae8dd19ad8",
    model="llama-v2-13b-chat",
    object="chat.completion",
    created=1703302755,
    choices=[
        Choice(
            finish_reason="stop",
            index=0,
            message=ChatCompletionMessage(role="assistant", content=resp_content),
            logprobs=None,
        )
    ],
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
)

prompt_msg = "who are you"
messages = [{"role": "user", "content": prompt_msg}]


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

    openllm_gpt = OpenLLM()
    openllm_gpt.model = "llama-v2-13b-chat"

    openllm_gpt._update_costs(usage=CompletionUsage(prompt_tokens=100, completion_tokens=100, total_tokens=200))
    assert openllm_gpt.get_costs() == Costs(
        total_prompt_tokens=100, total_completion_tokens=100, total_cost=0, total_budget=0
    )

    resp = await openllm_gpt.acompletion(messages)
    assert resp.choices[0].message.content in resp_content

    resp = await openllm_gpt.aask(prompt_msg, stream=False)
    assert resp == resp_content

    resp = await openllm_gpt.acompletion_text(messages, stream=False)
    assert resp == resp_content

    resp = await openllm_gpt.acompletion_text(messages, stream=True)
    assert resp == resp_content

    resp = await openllm_gpt.aask(prompt_msg)
    assert resp == resp_content
