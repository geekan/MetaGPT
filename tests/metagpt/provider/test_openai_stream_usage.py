import pytest
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletionChunk

from metagpt.configs.llm_config import LLMConfig
from metagpt.provider.openai_api import OpenAILLM
from metagpt.utils.cost_manager import CostManager


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "usage_location, usage_as_dict",
    [
        ("empty_choices", False),
        ("empty_choices", True),
        ("finish_chunk", False),
        ("finish_chunk", True),
        ("choice", True),
        (None, False),
    ],
)
async def test_openai_stream_usage(mocker, usage_location, usage_as_dict):
    llm = OpenAILLM(LLMConfig(api_key="test-key", model="custom-model"))
    llm.cost_manager = CostManager()
    messages = [{"role": "user", "content": "Hello"}]
    server_usage = CompletionUsage(prompt_tokens=4, completion_tokens=2, total_tokens=6)
    fallback_usage = CompletionUsage(prompt_tokens=7, completion_tokens=3, total_tokens=10)
    calculate_usage = mocker.patch.object(llm, "_calc_usage", return_value=fallback_usage)
    common = {"id": "test-stream", "created": 0, "model": "custom-model", "object": "chat.completion.chunk"}
    empty_chunk = ChatCompletionChunk(**common, choices=[])
    chunks = [
        empty_chunk,
        ChatCompletionChunk(
            **common,
            choices=[{"index": 0, "delta": {"content": "Hello"}, "finish_reason": None}],
        ),
        ChatCompletionChunk(**common, choices=[{"index": 0, "delta": {}, "finish_reason": "stop"}]),
    ]
    usage = server_usage.model_dump() if usage_as_dict else server_usage
    if usage_location == "empty_choices":
        chunks.append(empty_chunk.model_copy(update={"usage": usage}))
    elif usage_location == "finish_chunk":
        chunks[-1] = chunks[-1].model_copy(update={"usage": usage})
    elif usage_location == "choice":
        chunks[-1].choices[0] = chunks[-1].choices[0].model_copy(update={"usage": usage})
    chunks.append(empty_chunk)

    async def response_chunks():
        for chunk in chunks:
            yield chunk

    mocker.patch.object(llm.aclient.chat.completions, "create", new=mocker.AsyncMock(return_value=response_chunks()))
    try:
        assert await llm.acompletion_text(messages, stream=True) == "Hello"
        expected = server_usage if usage_location else fallback_usage
        assert llm.cost_manager.total_prompt_tokens == expected.prompt_tokens
        assert llm.cost_manager.total_completion_tokens == expected.completion_tokens
        if usage_location:
            calculate_usage.assert_not_called()
        else:
            calculate_usage.assert_called_once_with(messages, "Hello")
    finally:
        await llm.aclient.close()
