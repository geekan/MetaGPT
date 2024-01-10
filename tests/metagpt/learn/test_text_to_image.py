#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18
@Author  : mashenquan
@File    : test_text_to_image.py
@Desc    : Unit tests.
"""


import pytest

from metagpt.config2 import Config
from metagpt.learn.text_to_image import text_to_image
from metagpt.tools.metagpt_text_to_image import MetaGPTText2Image
from metagpt.tools.openai_text_to_image import OpenAIText2Image
from metagpt.utils.s3 import S3


@pytest.mark.asyncio
async def test_text_to_image(mocker):
    # mock
    mocker.patch.object(MetaGPTText2Image, "text_2_image", return_value=b"mock MetaGPTText2Image")
    mocker.patch.object(OpenAIText2Image, "text_2_image", return_value=b"mock OpenAIText2Image")
    mocker.patch.object(S3, "cache", return_value="http://mock/s3")

    config = Config.default()
    assert config.METAGPT_TEXT_TO_IMAGE_MODEL_URL

    data = await text_to_image(
        "Panda emoji", size_type="512x512", model_url=config.METAGPT_TEXT_TO_IMAGE_MODEL_URL, config=config
    )
    assert "base64" in data or "http" in data


@pytest.mark.asyncio
async def test_openai_text_to_image():
    config = Config.default()
    assert config.get_openai_llm()

    data = await text_to_image("Panda emoji", size_type="512x512", config=config)
    assert "base64" in data or "http" in data


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
