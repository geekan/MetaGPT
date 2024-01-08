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

default_chat_resp = {
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "I'am GPT",
            },
            "finish_reason": "stop",
        }
    ]
}
prompt_msg = "who are you"
resp_content = default_chat_resp["choices"][0]["message"]["content"]


class MockBaseLLM(BaseLLM):
    def __init__(self, config: LLMConfig = None):
        pass

    def completion(self, messages: list[dict], timeout=3):
        return default_chat_resp

    async def acompletion(self, messages: list[dict], timeout=3):
        return default_chat_resp

    async def acompletion_text(self, messages: list[dict], stream=False, timeout=3) -> str:
        return resp_content

    async def close(self):
        return default_chat_resp


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

    # resp = base_llm.ask(prompt_msg)
    # assert resp == resp_content

    # resp = base_llm.ask_batch([prompt_msg])
    # assert resp == resp_content

    # resp = base_llm.ask_code([prompt_msg])
    # assert resp == resp_content


@pytest.mark.asyncio
async def test_async_base_llm():
    base_llm = MockBaseLLM()

    resp = await base_llm.aask(prompt_msg)
    assert resp == resp_content

    resp = await base_llm.aask_batch([prompt_msg])
    assert resp == resp_content

    # resp = await base_llm.aask_code([prompt_msg])
    # assert resp == resp_content
