#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of spark api

import pytest

from metagpt.provider.spark_api import SparkLLM

prompt_msg = "who are you"
resp_content = "I'm Spark"


def mock_llm_completion(self, messages: list[dict], timeout: int = 60) -> str:
    return resp_content


async def mock_llm_acompletion(self, messgaes: list[dict], stream: bool = False, timeout: int = 60) -> str:
    return resp_content


@pytest.mark.asyncio
async def test_spark_acompletion(mocker):
    mocker.patch("metagpt.provider.spark_api.SparkGPTAPI.acompletion", mock_llm_acompletion)
    mocker.patch("metagpt.provider.spark_api.SparkGPTAPI.acompletion_text", mock_llm_acompletion)
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
