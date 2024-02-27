#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of DashScopeLLM

from typing import AsyncGenerator, Union

import pytest
from dashscope.api_entities.dashscope_response import GenerationResponse

from metagpt.provider.dashscope_api import DashScopeLLM
from tests.metagpt.provider.mock_llm_config import mock_llm_config_dashscope
from tests.metagpt.provider.req_resp_const import (
    get_dashscope_response,
    llm_general_chat_funcs_test,
    messages,
    prompt,
    resp_cont_tmpl,
)

name = "qwen-max"
resp_cont = resp_cont_tmpl.format(name=name)


@classmethod
def mock_dashscope_call(
    cls,
    messages: list[dict],
    model: str,
    api_key: str,
    result_format: str,
    incremental_output: bool = True,
    stream: bool = False,
) -> GenerationResponse:
    return get_dashscope_response(name)


@classmethod
async def mock_dashscope_acall(
    cls,
    messages: list[dict],
    model: str,
    api_key: str,
    result_format: str,
    incremental_output: bool = True,
    stream: bool = False,
) -> Union[AsyncGenerator[GenerationResponse, None], GenerationResponse]:
    resps = [get_dashscope_response(name)]

    if stream:

        async def aresp_iterator(resps: list[GenerationResponse]):
            for resp in resps:
                yield resp

        return aresp_iterator(resps)
    else:
        return resps[0]


@pytest.mark.asyncio
async def test_dashscope_acompletion(mocker):
    mocker.patch("dashscope.aigc.generation.Generation.call", mock_dashscope_call)
    mocker.patch("metagpt.provider.dashscope_api.AGeneration.acall", mock_dashscope_acall)

    dashscope_llm = DashScopeLLM(mock_llm_config_dashscope)

    resp = dashscope_llm.completion(messages)
    assert resp.choices[0]["message"]["content"] == resp_cont

    resp = await dashscope_llm.acompletion(messages)
    assert resp.choices[0]["message"]["content"] == resp_cont

    await llm_general_chat_funcs_test(dashscope_llm, prompt, messages, resp_cont)
