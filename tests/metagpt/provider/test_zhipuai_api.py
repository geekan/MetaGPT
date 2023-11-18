#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of ZhiPuAIGPTAPI

import pytest

from metagpt.provider.zhipuai_api import ZhiPuAIGPTAPI


default_resp = {
    "code": 200,
    "data": {
        "choices": [
            {"role": "assistant", "content": "I'm chatglm-turbo"}
        ]
    }
}

messages = [
    {"role": "user", "content": "who are you"}
]


def mock_llm_ask(self, messages: list[dict]) -> dict:
    return default_resp


def test_zhipuai_completion(mocker):
    mocker.patch("metagpt.provider.zhipuai_api.ZhiPuAIGPTAPI.completion", mock_llm_ask)

    resp = ZhiPuAIGPTAPI().completion(messages)
    assert resp["code"] == 200
    assert "chatglm-turbo" in resp["data"]["choices"][0]["content"]


async def mock_llm_aask(self, messgaes: list[dict], stream: bool = False) -> dict:
    return default_resp


@pytest.mark.asyncio
async def test_zhipuai_acompletion(mocker):
    mocker.patch("metagpt.provider.zhipuai_api.ZhiPuAIGPTAPI.acompletion_text", mock_llm_aask)

    resp = await ZhiPuAIGPTAPI().acompletion_text(messages, stream=False)

    assert resp["code"] == 200
    assert "chatglm-turbo" in resp["data"]["choices"][0]["content"]
