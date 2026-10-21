"""Exercise MiniMax requests through the real SDK with an offline HTTP transport."""

import json

import httpx
import pytest

from metagpt.config2 import Config
from metagpt.configs.llm_config import LLMConfig
from metagpt.provider.llm_provider_registry import create_llm_instance
from metagpt.provider.minimax_api import MiniMaxLLM
from metagpt.utils.token_counter import TOKEN_COSTS, TOKEN_MAX


@pytest.mark.parametrize("model", [None, "MiniMax-M3.1-Flash", "MiniMax-M3", "MiniMax-M2.7", "custom-model"])
@pytest.mark.parametrize("base_url", [None, "https://api.minimaxi.com/v1", "https://custom.invalid/v1"])
@pytest.mark.asyncio
async def test_minimax_http_defaults_and_saved_config(monkeypatch, model, base_url):
    values = {"api_type": "minimax", "api_key": "offline-fixture", "calc_usage": False}
    if model is not None:
        values["model"] = model
    if base_url is not None:
        values["base_url"] = base_url
    config = Config.from_llm_config(values).llm
    saved = config.model_dump(exclude_none=True)
    expected_model = model or "MiniMax-M3.1-Flash"
    expected_url = base_url or "https://api.minimax.io/v1"
    history = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this"},
                {"type": "image_url", "image_url": {"url": "https://example.invalid/image.png"}},
            ],
        },
        {
            "role": "assistant",
            "content": None,
            "reasoning_content": "Inspect the result",
            "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "lookup", "arguments": "{}"}}],
        },
        {"role": "tool", "tool_call_id": "call_1", "content": "result"},
    ]
    tools = [{"type": "function", "function": {"name": "lookup", "parameters": {"type": "object"}}}]
    captured = []

    def handle(request):
        body = json.loads(request.content)
        captured.append(body)
        assert str(request.url) == expected_url + "/chat/completions"
        assert body["model"] == expected_model
        assert body["messages"] == history
        assert 0 < body["temperature"] <= 1
        assert body["max_tokens"] == 4096
        assert "service_tier" not in body
        assert "thinking" not in body
        assert "reasoning_split" not in body
        response = {
            "id": "fixture",
            "object": "chat.completion",
            "created": 1,
            "model": expected_model,
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": "done", "reasoning_content": "kept"},
                }
            ],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
        if body.get("stream"):
            chunk = {
                "id": "fixture",
                "object": "chat.completion.chunk",
                "created": 1,
                "model": expected_model,
                "choices": [{"index": 0, "finish_reason": "stop", "delta": {"content": "done"}}],
            }
            reasoning_chunk = {
                **chunk,
                "choices": [{"index": 0, "finish_reason": None, "delta": {"reasoning_content": "stream reasoning"}}],
            }
            return httpx.Response(
                200,
                text="data: " + json.dumps(reasoning_chunk) + "\n\ndata: " + json.dumps(chunk) + "\n\ndata: [DONE]\n\n",
                headers={"content-type": "text/event-stream"},
            )
        return httpx.Response(200, json=response)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        original = MiniMaxLLM._make_client_kwargs

        def client_kwargs(self):
            return {**original(self), "http_client": client}

        monkeypatch.setattr(MiniMaxLLM, "_make_client_kwargs", client_kwargs)
        llm = create_llm_instance(LLMConfig(**saved))
        assert isinstance(llm, MiniMaxLLM)
        response = await llm.acompletion(history)
        assert response.choices[0].message.reasoning_content == "kept"
        assert await llm.acompletion_text(history, stream=True) == "done"
        assert llm.reasoning_content == "stream reasoning"
        await llm._achat_completion_function(history, tools=tools, reasoning_effort="high")
    assert len(captured) == 3
    assert captured[-1]["tools"] == tools
    assert captured[-1]["reasoning_effort"] == "high"
    assert "reasoning_effort" not in captured[0]
    assert config.model_dump(exclude_none=True) == saved


def test_minimax_metadata_and_other_defaults():
    config = LLMConfig(api_key="offline-fixture")
    assert config.model is None
    assert config.base_url == "https://api.openai.com/v1"
    assert TOKEN_MAX["MiniMax-M3.1-Flash"] == TOKEN_MAX["MiniMax-M3"] == 1000000
    assert TOKEN_COSTS["MiniMax-M3.1-Flash"] == {"prompt": 0.00015, "completion": 0.0006}
    assert TOKEN_COSTS["MiniMax-M3"] == {"prompt": 0.0003, "completion": 0.0012}
