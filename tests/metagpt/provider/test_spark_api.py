#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of spark api

import pytest

from metagpt.config import CONFIG
from metagpt.provider.spark_api import GetMessageFromWeb, SparkLLM

CONFIG.spark_appid = "xxx"
CONFIG.spark_api_secret = "xxx"
CONFIG.spark_api_key = "xxx"
CONFIG.domain = "xxxxxx"
CONFIG.spark_url = "xxxx"

prompt_msg = "who are you"
resp_content = "I'm Spark"


class MockWebSocketApp(object):
    def __init__(self, ws_url, on_message=None, on_error=None, on_close=None, on_open=None):
        pass

    def run_forever(self, sslopt=None):
        pass


def test_get_msg_from_web(mocker):
    mocker.patch("websocket.WebSocketApp", MockWebSocketApp)

    get_msg_from_web = GetMessageFromWeb(text=prompt_msg)
    assert get_msg_from_web.gen_params()["parameter"]["chat"]["domain"] == "xxxxxx"

    ret = get_msg_from_web.run()
    assert ret == ""


def mock_spark_get_msg_from_web_run(self) -> str:
    return resp_content


@pytest.mark.asyncio
async def test_spark_acompletion(mocker):
    mocker.patch("metagpt.provider.spark_api.GetMessageFromWeb.run", mock_spark_get_msg_from_web_run)

    spark_gpt = SparkLLM()

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
