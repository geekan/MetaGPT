#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of ZhiPuAILLM

import pytest
from zhipuai.utils.sse_client import Event

from metagpt.config import CONFIG
from metagpt.provider.zhipuai_api import ZhiPuAILLM

CONFIG.zhipuai_api_key = "xxx.xxx"

prompt_msg = "who are you"
messages = [{"role": "user", "content": prompt_msg}]

resp_content = "I'm chatglm-turbo"
default_resp = {
    "code": 200,
    "data": {
        "choices": [{"role": "assistant", "content": resp_content}],
        "usage": {"prompt_tokens": 20, "completion_tokens": 20},
    },
}


def mock_zhipuai_invoke(**kwargs) -> dict:
    return default_resp


async def mock_zhipuai_ainvoke(**kwargs) -> dict:
    return default_resp


async def mock_zhipuai_asse_invoke(**kwargs):
    class MockResponse(object):
        async def _aread(self):
            class Iterator(object):
                events = [
                    Event(id="xxx", event="add", data=resp_content, retry=0),
                    Event(
                        id="xxx",
                        event="finish",
                        data="",
                        meta='{"usage": {"completion_tokens": 20,"prompt_tokens": 20}}',
                    ),
                ]

                async def __aiter__(self):
                    for event in self.events:
                        yield event

            async for chunk in Iterator():
                yield chunk

        async def async_events(self):
            async for chunk in self._aread():
                yield chunk

    return MockResponse()


@pytest.mark.asyncio
async def test_zhipuai_acompletion(mocker):
    mocker.patch("metagpt.provider.zhipuai.zhipu_model_api.ZhiPuModelAPI.invoke", mock_zhipuai_invoke)
    mocker.patch("metagpt.provider.zhipuai.zhipu_model_api.ZhiPuModelAPI.ainvoke", mock_zhipuai_ainvoke)
    mocker.patch("metagpt.provider.zhipuai.zhipu_model_api.ZhiPuModelAPI.asse_invoke", mock_zhipuai_asse_invoke)

    zhipu_gpt = ZhiPuAILLM()

    resp = await zhipu_gpt.acompletion(messages)
    assert resp["data"]["choices"][0]["content"] == resp_content

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
