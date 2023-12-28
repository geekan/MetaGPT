#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of ZhiPuAIGPTAPI

import pytest

from metagpt.config import CONFIG
from metagpt.provider.zhipuai_api import ZhiPuAIGPTAPI

CONFIG.zhipuai_api_key = "xxx"

prompt_msg = "who are you"
messages = [{"role": "user", "content": prompt_msg}]

resp_content = "I'm chatglm-turbo"
default_resp = {"code": 200, "data": {"choices": [{"role": "assistant", "content": resp_content}]}}


def mock_llm_completion(self, messages: list[dict], timeout: int = 60) -> dict:
    return default_resp


async def mock_llm_acompletion(self, messgaes: list[dict], stream: bool = False, timeout: int = 60) -> dict:
    return default_resp


async def mock_llm_achat_completion_stream(self, messgaes: list[dict]) -> str:
    return resp_content


@pytest.mark.asyncio
async def test_zhipuai_acompletion(mocker):
    mocker.patch("metagpt.provider.zhipuai_api.ZhiPuAIGPTAPI.acompletion", mock_llm_acompletion)
    mocker.patch("metagpt.provider.zhipuai_api.ZhiPuAIGPTAPI._achat_completion", mock_llm_acompletion)
    mocker.patch(
        "metagpt.provider.zhipuai_api.ZhiPuAIGPTAPI._achat_completion_stream", mock_llm_achat_completion_stream
    )
    zhipu_gpt = ZhiPuAIGPTAPI()

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


def test_zhipuai_proxy(mocker):
    import openai

    from metagpt.config import CONFIG

    CONFIG.openai_proxy = "http://127.0.0.1:8080"
    _ = ZhiPuAIGPTAPI()
    assert openai.proxy == CONFIG.openai_proxy
