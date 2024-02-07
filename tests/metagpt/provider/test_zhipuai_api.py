#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of ZhiPuAILLM

import pytest

from metagpt.provider.zhipuai_api import ZhiPuAILLM
from tests.metagpt.provider.mock_llm_config import mock_llm_config_zhipu
from tests.metagpt.provider.req_resp_const import (
    get_part_chat_completion,
    llm_general_chat_funcs_test,
    messages,
    prompt,
    resp_cont_tmpl,
)

name = "ChatGLM-4"
resp_cont = resp_cont_tmpl.format(name=name)
default_resp = get_part_chat_completion(name)


async def mock_zhipuai_acreate_stream(self, **kwargs):
    class MockResponse(object):
        async def _aread(self):
            class Iterator(object):
                events = [{"choices": [{"index": 0, "delta": {"content": resp_cont, "role": "assistant"}}]}]

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

    zhipu_llm = ZhiPuAILLM(mock_llm_config_zhipu)

    resp = await zhipu_llm.acompletion(messages)
    assert resp["choices"][0]["message"]["content"] == resp_cont

    await llm_general_chat_funcs_test(zhipu_llm, prompt, messages, resp_cont)


def test_zhipuai_proxy():
    # it seems like zhipuai would be inflected by the proxy of openai, maybe it's a bug
    # but someone may want to use openai.proxy, so we keep this test case
    # assert openai.proxy == config.llm.proxy
    _ = ZhiPuAILLM(mock_llm_config_zhipu)
