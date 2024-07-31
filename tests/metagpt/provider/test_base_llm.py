#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/7 17:40
@Author  : alexanderwu
@File    : test_base_llm.py
"""

import pytest

from metagpt.configs.llm_config import LLMConfig
from metagpt.provider.base_llm import BaseLLM
from metagpt.schema import Message
from tests.metagpt.provider.mock_llm_config import mock_llm_config
from tests.metagpt.provider.req_resp_const import (
    default_resp_cont,
    get_part_chat_completion,
    prompt,
)

name = "GPT"


class MockBaseLLM(BaseLLM):
    def __init__(self, config: LLMConfig = None):
        self.config = config or mock_llm_config

    def completion(self, messages: list[dict], timeout=3):
        return get_part_chat_completion(name)

    async def _achat_completion(self, messages: list[dict], timeout=3):
        pass

    async def acompletion(self, messages: list[dict], timeout=3):
        return get_part_chat_completion(name)

    async def _achat_completion_stream(self, messages: list[dict], timeout: int = 3) -> str:
        pass

    async def acompletion_text(self, messages: list[dict], stream=False, timeout=3) -> str:
        return default_resp_cont


def test_base_llm():
    message = Message(role="user", content="hello")
    assert "role" in message.to_dict()
    assert "user" in str(message)

    base_llm = MockBaseLLM()

    openai_funccall_resp = {
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "test",
                    "tool_calls": [
                        {
                            "id": "call_Y5r6Ddr2Qc2ZrqgfwzPX5l72",
                            "type": "function",
                            "function": {
                                "name": "execute",
                                "arguments": '{\n  "language": "python",\n  "code": "print(\'Hello, World!\')"\n}',
                            },
                        }
                    ],
                },
                "finish_reason": "stop",
            }
        ]
    }
    func: dict = base_llm.get_choice_function(openai_funccall_resp)
    assert func == {
        "name": "execute",
        "arguments": '{\n  "language": "python",\n  "code": "print(\'Hello, World!\')"\n}',
    }

    func_args: dict = base_llm.get_choice_function_arguments(openai_funccall_resp)
    assert func_args == {"language": "python", "code": "print('Hello, World!')"}

    choice_text = base_llm.get_choice_text(openai_funccall_resp)
    assert choice_text == openai_funccall_resp["choices"][0]["message"]["content"]

    # resp = base_llm.ask(prompt)
    # assert resp == default_resp_cont

    # resp = base_llm.ask_batch([prompt])
    # assert resp == default_resp_cont

    # resp = base_llm.ask_code([prompt])
    # assert resp == default_resp_cont


@pytest.mark.asyncio
async def test_async_base_llm():
    base_llm = MockBaseLLM()

    resp = await base_llm.aask(prompt)
    assert resp == default_resp_cont

    resp = await base_llm.aask_batch([prompt])
    assert resp == default_resp_cont

    # resp = await base_llm.aask_code([prompt])
    # assert resp == default_resp_cont


@pytest.mark.parametrize(
    "compress_type", ["post_cut_by_msg", "post_cut_by_token", "pre_cut_by_msg", "pre_cut_by_token"]
)
def test_compress_messages_no_effect(compress_type):
    base_llm = MockBaseLLM()
    messages = [
        {"role": "system", "content": "first system msg"},
        {"role": "system", "content": "second system msg"},
    ]
    for i in range(5):
        messages.append({"role": "user", "content": f"u{i}"})
        messages.append({"role": "assistant", "content": f"a{i}"})
    compressed = base_llm.compress_messages(messages, compress_type=compress_type)
    # should take no effect for short context
    assert compressed == messages


@pytest.mark.parametrize(
    "compress_type", ["post_cut_by_msg", "post_cut_by_token", "pre_cut_by_msg", "pre_cut_by_token"]
)
def test_compress_messages_long(compress_type):
    base_llm = MockBaseLLM()
    base_llm.config.model = "test_llm"
    max_token_limit = 100

    messages = [
        {"role": "system", "content": "first system msg"},
        {"role": "system", "content": "second system msg"},
    ]
    for i in range(100):
        messages.append({"role": "user", "content": f"u{i}" * 10})  # ~2x10x0.5 = 10 tokens
        messages.append({"role": "assistant", "content": f"a{i}" * 10})
    compressed = base_llm.compress_messages(messages, compress_type=compress_type, max_token=max_token_limit)

    print(compressed)
    print(len(compressed))
    assert len(compressed) < len(messages)
    assert compressed[0]["role"] == "system" and compressed[1]["role"] == "system"
    assert compressed[2]["role"] != "system"


@pytest.mark.parametrize(
    "compress_type", ["post_cut_by_msg", "post_cut_by_token", "pre_cut_by_msg", "pre_cut_by_token"]
)
def test_compress_messages_long_no_sys_msg(compress_type):
    base_llm = MockBaseLLM()
    base_llm.config.model = "test_llm"
    max_token_limit = 100

    messages = [{"role": "user", "content": "1" * 10000}]
    compressed = base_llm.compress_messages(messages, compress_type=compress_type, max_token=max_token_limit)

    print(compressed)
    assert compressed
    assert len(compressed[0]["content"]) < len(messages[0]["content"])
