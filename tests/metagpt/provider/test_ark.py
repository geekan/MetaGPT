"""
用于火山方舟Python SDK V3的测试用例
API文档：https://www.volcengine.com/docs/82379/1263482
"""

from typing import AsyncIterator, List, Union

import pytest
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice, ChoiceDelta

from metagpt.provider.ark_api import ArkLLM
from tests.metagpt.provider.mock_llm_config import mock_llm_config_ark
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
default_resp.model = "doubao-pro-32k-240515"
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
        model="doubao-pro-32k-240515",
        object="chat.completion.chunk",
        system_fingerprint=None,
        usage=None if choices else USAGE,
    )


ark_resp_chunk = create_chat_completion_chunk(content="")
ark_resp_chunk_finish = create_chat_completion_chunk(content=resp_cont, finish_reason="stop")
ark_resp_chunk_last = create_chat_completion_chunk(content="", choices=[])


async def chunk_iterator(chunks: List[ChatCompletionChunk]) -> AsyncIterator[ChatCompletionChunk]:
    for chunk in chunks:
        yield chunk


async def mock_ark_acompletions_create(
    self, stream: bool = False, **kwargs
) -> Union[ChatCompletionChunk, ChatCompletion]:
    if stream:
        chunks = [ark_resp_chunk, ark_resp_chunk_finish, ark_resp_chunk_last]
        return chunk_iterator(chunks)
    else:
        return default_resp


@pytest.mark.asyncio
async def test_ark_acompletion(mocker):
    mocker.patch("openai.resources.chat.completions.AsyncCompletions.create", mock_ark_acompletions_create)

    llm = ArkLLM(mock_llm_config_ark)

    resp = await llm.acompletion(messages)
    assert resp.choices[0].finish_reason == "stop"
    assert resp.choices[0].message.content == resp_cont
    assert resp.usage == USAGE

    await llm_general_chat_funcs_test(llm, prompt, messages, resp_cont)
