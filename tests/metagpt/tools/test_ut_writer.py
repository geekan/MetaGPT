#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/30 21:44
@Author  : alexanderwu
@File    : test_ut_writer.py
"""
from pathlib import Path

import pytest
from openai.resources.chat.completions import AsyncCompletions
from openai.types import CompletionUsage
from openai.types.chat.chat_completion import (
    ChatCompletion,
    ChatCompletionMessage,
    Choice,
)
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)

from metagpt.config2 import config
from metagpt.const import API_QUESTIONS_PATH, UT_PY_PATH
from metagpt.tools.ut_writer import YFT_PROMPT_PREFIX, UTGenerator


class TestUTWriter:
    @pytest.mark.asyncio
    async def test_api_to_ut_sample(self, mocker):
        async def mock_create(*args, **kwargs):
            return ChatCompletion(
                id="chatcmpl-8n5fAd21w2J1IIFkI4qxWlNfM7QRC",
                choices=[
                    Choice(
                        finish_reason="stop",
                        index=0,
                        logprobs=None,
                        message=ChatCompletionMessage(
                            content=None,
                            role="assistant",
                            function_call=None,
                            tool_calls=[
                                ChatCompletionMessageToolCall(
                                    id="call_EjjmIY7GMspHu3r9mx8gPA2k",
                                    function=Function(
                                        arguments='{"code":"import string\\nimport random\\n\\ndef random_string'
                                        "(length=10):\\n    return ''.join(random.choice(string.ascii_"
                                        'lowercase) for i in range(length))"}',
                                        name="execute",
                                    ),
                                    type="function",
                                )
                            ],
                        ),
                    )
                ],
                created=1706710532,
                model="gpt-3.5-turbo-1106",
                object="chat.completion",
                system_fingerprint="fp_04f9a1eebf",
                usage=CompletionUsage(completion_tokens=35, prompt_tokens=1982, total_tokens=2017),
            )

        mocker.patch.object(AsyncCompletions, "create", mock_create)

        # Prerequisites
        swagger_file = Path(__file__).parent / "../../data/ut_writer/yft_swaggerApi.json"
        assert swagger_file.exists()
        assert config.get_openai_llm()

        tags = ["测试", "作业"]
        # 这里在文件中手动加入了两个测试标签的API

        utg = UTGenerator(
            swagger_file=str(swagger_file),
            ut_py_path=UT_PY_PATH,
            questions_path=API_QUESTIONS_PATH,
            template_prefix=YFT_PROMPT_PREFIX,
        )
        ret = await utg.generate_ut(include_tags=tags)
        # 后续加入对文件生成内容与数量的检验
        assert ret


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
