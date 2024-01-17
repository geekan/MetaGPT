#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of ZhiPuAILLM

import pytest

from metagpt.config import CONFIG
from metagpt.provider.zhipuai_api import ZhiPuAILLM

CONFIG.zhipuai_api_key = "xxx.xxx"

prompt_msg = "who are you"
messages = [{"role": "user", "content": prompt_msg}]

resp_content = "I'm chatglm-turbo"
default_resp = {
    "choices": [{"finish_reason": "stop", "index": 0, "message": {"content": resp_content, "role": "assistant"}}],
    "usage": {"completion_tokens": 22, "prompt_tokens": 19, "total_tokens": 41},
}


async def mock_zhipuai_acreate_stream(self, **kwargs):
    class MockResponse(object):
        async def _aread(self):
            class Iterator(object):
                events = [{"choices": [{"index": 0, "delta": {"content": resp_content, "role": "assistant"}}]}]

                async def __aiter__(self):
                    for event in self.events:
                        yield event

            async for chunk in Iterator():
                yield chunk

        async def stream(self):
            async for chunk in self._aread():
                yield chunk

    return MockResponse()


async def mock_zhipuai_acreate(self, **kwargs) -> dict:
    return default_resp


@pytest.mark.asyncio
async def test_zhipuai_acompletion(mocker):
    mocker.patch("metagpt.provider.zhipuai.zhipu_model_api.ZhiPuModelAPI.acreate", mock_zhipuai_acreate)
    mocker.patch("metagpt.provider.zhipuai.zhipu_model_api.ZhiPuModelAPI.acreate_stream", mock_zhipuai_acreate_stream)

    zhipu_gpt = ZhiPuAILLM()

    resp = await zhipu_gpt.acompletion(messages)
    assert resp["choices"][0]["message"]["content"] == resp_content

    resp = await zhipu_gpt.aask(prompt_msg, stream=False)
    assert resp == resp_content

    resp = await zhipu_gpt.acompletion_text(messages, stream=False)
    assert resp == resp_content

    resp = await zhipu_gpt.acompletion_text(messages, stream=True)
    assert resp == resp_content

    resp = await zhipu_gpt.aask(prompt_msg)
    assert resp == resp_content


def test_zhipuai_proxy():
    # CONFIG.openai_proxy = "http://127.0.0.1:8080"
    _ = ZhiPuAILLM()
    # assert openai.proxy == CONFIG.openai_proxy
