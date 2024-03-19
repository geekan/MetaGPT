#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of spark api

import pytest

from metagpt.provider.spark_api import GetMessageFromWeb, SparkLLM
from tests.metagpt.provider.mock_llm_config import (
    mock_llm_config,
    mock_llm_config_spark,
)
from tests.metagpt.provider.req_resp_const import (
    llm_general_chat_funcs_test,
    prompt,
    resp_cont_tmpl,
)

resp_cont = resp_cont_tmpl.format(name="Spark")


class MockWebSocketApp(object):
    def __init__(self, ws_url, on_message=None, on_error=None, on_close=None, on_open=None):
        pass

    def run_forever(self, sslopt=None):
        pass


def test_get_msg_from_web(mocker):
    mocker.patch("websocket.WebSocketApp", MockWebSocketApp)

    get_msg_from_web = GetMessageFromWeb(prompt, mock_llm_config)
    assert get_msg_from_web.gen_params()["parameter"]["chat"]["domain"] == "mock_domain"

    ret = get_msg_from_web.run()
    assert ret == ""


def mock_spark_get_msg_from_web_run(self) -> str:
    return resp_cont


@pytest.mark.asyncio
async def test_spark_aask(mocker):
    mocker.patch("metagpt.provider.spark_api.GetMessageFromWeb.run", mock_spark_get_msg_from_web_run)

    llm = SparkLLM(mock_llm_config_spark)

    resp = await llm.aask("Hello!")
    assert resp == resp_cont


@pytest.mark.asyncio
async def test_spark_acompletion(mocker):
    mocker.patch("metagpt.provider.spark_api.GetMessageFromWeb.run", mock_spark_get_msg_from_web_run)

    spark_llm = SparkLLM(mock_llm_config)

    resp = await spark_llm.acompletion([])
    assert resp == resp_cont

    await llm_general_chat_funcs_test(spark_llm, prompt, prompt, resp_cont)
