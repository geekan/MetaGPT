#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of spark api

import pytest

from metagpt.config2 import Config
from metagpt.provider.spark_api import GetMessageFromWeb, SparkLLM
from tests.metagpt.provider.mock_llm_config import mock_llm_config

prompt_msg = "who are you"
resp_content = "I'm Spark"


class MockWebSocketApp(object):
    def __init__(self, ws_url, on_message=None, on_error=None, on_close=None, on_open=None):
        pass

    def run_forever(self, sslopt=None):
        pass


def test_get_msg_from_web(mocker):
    mocker.patch("websocket.WebSocketApp", MockWebSocketApp)

    get_msg_from_web = GetMessageFromWeb(prompt_msg, mock_llm_config)
    assert get_msg_from_web.gen_params()["parameter"]["chat"]["domain"] == "mock_domain"

    ret = get_msg_from_web.run()
    assert ret == ""


def mock_spark_get_msg_from_web_run(self) -> str:
    return resp_content


@pytest.mark.asyncio
async def test_spark_aask():
    llm = SparkLLM(Config.from_home("spark.yaml").llm)

    resp = await llm.aask("Hello!")
    print(resp)


@pytest.mark.asyncio
async def test_spark_acompletion(mocker):
    mocker.patch("metagpt.provider.spark_api.GetMessageFromWeb.run", mock_spark_get_msg_from_web_run)

    spark_gpt = SparkLLM(mock_llm_config)

    resp = await spark_gpt.acompletion([])
    assert resp == resp_content

    resp = await spark_gpt.aask(prompt_msg, stream=False)
    assert resp == resp_content

    resp = await spark_gpt.acompletion_text([], stream=False)
    assert resp == resp_content

    resp = await spark_gpt.acompletion_text([], stream=True)
    assert resp == resp_content

    resp = await spark_gpt.aask(prompt_msg)
    assert resp == resp_content
