#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of qianfan api

from typing import AsyncIterator, Union

import pytest
from qianfan.resources.typing import JsonBody, QfResponse

from metagpt.provider.qianfan_api import QianFanLLM
from tests.metagpt.provider.mock_llm_config import mock_llm_config_qianfan
from tests.metagpt.provider.req_resp_const import (
    get_qianfan_response,
    llm_general_chat_funcs_test,
    messages,
    prompt,
    resp_cont_tmpl,
)

name = "ERNIE-Bot-turbo"
resp_cont = resp_cont_tmpl.format(name=name)


def mock_qianfan_do(self, messages: list[dict], model: str, stream: bool = False, system: str = None) -> QfResponse:
    return get_qianfan_response(name=name)


async def mock_qianfan_ado(
    self, messages: list[dict], model: str, stream: bool = True, system: str = None
) -> Union[QfResponse, AsyncIterator[QfResponse]]:
    resps = [get_qianfan_response(name=name)]
    if stream:

        async def aresp_iterator(resps: list[JsonBody]):
            for resp in resps:
                yield resp

        return aresp_iterator(resps)
    else:
        return resps[0]


@pytest.mark.asyncio
async def test_qianfan_acompletion(mocker):
    mocker.patch("qianfan.resources.llm.chat_completion.ChatCompletion.do", mock_qianfan_do)
    mocker.patch("qianfan.resources.llm.chat_completion.ChatCompletion.ado", mock_qianfan_ado)

    qianfan_llm = QianFanLLM(mock_llm_config_qianfan)

    resp = qianfan_llm.completion(messages)
    assert resp.get("result") == resp_cont

    resp = await qianfan_llm.acompletion(messages)
    assert resp.get("result") == resp_cont

    await llm_general_chat_funcs_test(qianfan_llm, prompt, messages, resp_cont)
