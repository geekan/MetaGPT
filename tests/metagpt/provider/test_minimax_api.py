"""
Test cases for the MiniMax provider.
MiniMax exposes an OpenAI-compatible Chat Completions API.
API docs: https://platform.minimax.io/docs
"""

from typing import AsyncIterator, List, Union

import pytest
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice, ChoiceDelta

from metagpt.provider.minimax_api import MINIMAX_MAX_TEMPERATURE, MINIMAX_MIN_TEMPERATURE, MiniMaxLLM
from tests.metagpt.provider.mock_llm_config import mock_llm_config_minimax
from tests.metagpt.provider.req_resp_const import (
    get_openai_chat_completion,
    llm_general_chat_funcs_test,
    messages,
    prompt,
    resp_cont_tmpl,
)

name = "AI assistant"
resp_cont = resp_cont_tmpl.format(name=name)
USAGE = {"completion_tokens": 1000, "prompt_tokens": 1000, "total_tokens": 2000}
default_resp = get_openai_chat_completion(name)
default_resp.model = "MiniMax-M3"
default_resp.usage = USAGE


def create_chat_completion_chunk(
    content: str, finish_reason: str = None, choices: List[Choice] = None
) -> ChatCompletionChunk:
    if choices is None:
        choices = [
            Choice(
                delta=ChoiceDelta(content=content, function_call=None, role="assistant", tool_calls=None),
                finish_reason=finish_reason,
                index=0,
                logprobs=None,
            )
        ]

    return ChatCompletionChunk(
        id="012",
        choices=choices,
        created=1716278586,
        model="MiniMax-M3",
        object="chat.completion.chunk",
        system_fingerprint=None,
        usage=None if choices else USAGE,
    )


minimax_resp_chunk = create_chat_completion_chunk(content="")
minimax_resp_chunk_finish = create_chat_completion_chunk(content=resp_cont, finish_reason="stop")
minimax_resp_chunk_last = create_chat_completion_chunk(content="", choices=[])


async def chunk_iterator(chunks: List[ChatCompletionChunk]) -> AsyncIterator[ChatCompletionChunk]:
    for chunk in chunks:
        yield chunk


async def mock_minimax_acompletions_create(
    self, stream: bool = False, **kwargs
) -> Union[ChatCompletionChunk, ChatCompletion]:
    if stream:
        chunks = [minimax_resp_chunk, minimax_resp_chunk_finish, minimax_resp_chunk_last]
        return chunk_iterator(chunks)
    else:
        return default_resp


@pytest.mark.asyncio
async def test_minimax_acompletion(mocker):
    mocker.patch("openai.resources.chat.completions.AsyncCompletions.create", mock_minimax_acompletions_create)

    llm = MiniMaxLLM(mock_llm_config_minimax)

    resp = await llm.acompletion(messages)
    assert resp.choices[0].finish_reason == "stop"
    assert resp.choices[0].message.content == resp_cont
    assert resp.usage == USAGE

    await llm_general_chat_funcs_test(llm, prompt, messages, resp_cont)


def test_minimax_temperature_constraint():
    llm = MiniMaxLLM(mock_llm_config_minimax)
    kwargs = llm._cons_kwargs(messages)
    # temperature must be in (0.0, 1.0]
    assert MINIMAX_MIN_TEMPERATURE <= kwargs["temperature"] <= MINIMAX_MAX_TEMPERATURE
