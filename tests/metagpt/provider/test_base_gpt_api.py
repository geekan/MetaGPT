#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/7 17:40
@Author  : alexanderwu
@File    : test_base_gpt_api.py
"""

import pytest

from metagpt.provider.base_gpt_api import BaseGPTAPI
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


class MockBaseGPTAPI(BaseGPTAPI):
    def completion(self, messages: list[dict], timeout=3):
        return default_chat_resp

    async def acompletion(self, messages: list[dict], timeout=3):
        return default_chat_resp

    async def acompletion_text(self, messages: list[dict], stream=False, timeout=3) -> str:
        return resp_content

    async def close(self):
        return default_chat_resp


def test_base_gpt_api():
    message = Message(role="user", content="hello")
    assert "role" in message.to_dict()
    assert "user" in str(message)

    base_gpt_api = MockBaseGPTAPI()
    msg_prompt = base_gpt_api.messages_to_prompt([message])
    assert msg_prompt == "user: hello"

    msg_dict = base_gpt_api.messages_to_dict([message])
    assert msg_dict == [{"role": "user", "content": "hello"}]

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
    func: dict = base_gpt_api.get_choice_function(openai_funccall_resp)
    assert func == {
        "name": "execute",
        "arguments": '{\n  "language": "python",\n  "code": "print(\'Hello, World!\')"\n}',
    }

    func_args: dict = base_gpt_api.get_choice_function_arguments(openai_funccall_resp)
    assert func_args == {"language": "python", "code": "print('Hello, World!')"}

    choice_text = base_gpt_api.get_choice_text(openai_funccall_resp)
    assert choice_text == openai_funccall_resp["choices"][0]["message"]["content"]

    # resp = base_gpt_api.ask(prompt_msg)
    # assert resp == resp_content

    # resp = base_gpt_api.ask_batch([prompt_msg])
    # assert resp == resp_content

    # resp = base_gpt_api.ask_code([prompt_msg])
    # assert resp == resp_content


@pytest.mark.asyncio
async def test_async_base_gpt_api():
    base_gpt_api = MockBaseGPTAPI()

    resp = await base_gpt_api.aask(prompt_msg)
    assert resp == resp_content

    resp = await base_gpt_api.aask_batch([prompt_msg])
    assert resp == resp_content

    resp = await base_gpt_api.aask_code([prompt_msg])
    assert resp == resp_content
