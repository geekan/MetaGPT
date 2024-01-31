#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/26
@Author  : mashenquan
@File    : test_openai_text_to_image.py
"""
import base64

import openai
import pytest
from pydantic import BaseModel

from metagpt.config2 import config
from metagpt.llm import LLM
from metagpt.tools.openai_text_to_image import (
    OpenAIText2Image,
    oas3_openai_text_to_image,
)
from metagpt.utils.s3 import S3


@pytest.mark.asyncio
async def test_draw(mocker):
    # mock
    mock_url = mocker.Mock()
    mock_url.url.return_value = "http://mock.com/0.png"

    class _MockData(BaseModel):
        data: list

    mock_data = _MockData(data=[mock_url])
    mocker.patch.object(openai.resources.images.AsyncImages, "generate", return_value=mock_data)
    mock_post = mocker.patch("aiohttp.ClientSession.get")
    mock_response = mocker.AsyncMock()
    mock_response.status = 200
    mock_response.read.return_value = base64.b64encode(b"success")
    mock_post.return_value.__aenter__.return_value = mock_response
    mocker.patch.object(S3, "cache", return_value="http://mock.s3.com/0.png")

    # Prerequisites
    llm_config = config.get_openai_llm()
    assert llm_config

    binary_data = await oas3_openai_text_to_image("Panda emoji", llm=LLM(llm_config=llm_config))
    assert binary_data


@pytest.mark.asyncio
async def test_get_image():
    data = await OpenAIText2Image.get_image_data(
        url="https://www.baidu.com/img/PCtm_d9c8750bed0b3c7d089fa7d55720d6cf.png"
    )
    assert data


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
