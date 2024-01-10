#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/17
@Author  : mashenquan
@File    : openai_text_to_image.py
@Desc    : OpenAI Text-to-Image OAS3 api, which provides text-to-image functionality.
"""

import aiohttp
import requests

from metagpt.logs import logger
from metagpt.provider.base_llm import BaseLLM


class OpenAIText2Image:
    def __init__(self, llm: BaseLLM):
        self.llm = llm

    async def text_2_image(self, text, size_type="1024x1024"):
        """Text to image

        :param text: The text used for image conversion.
        :param size_type: One of ['256x256', '512x512', '1024x1024']
        :return: The image data is returned in Base64 encoding.
        """
        try:
            result = await self.llm.aclient.images.generate(prompt=text, n=1, size=size_type)
        except Exception as e:
            logger.error(f"An error occurred:{e}")
            return ""
        if result and len(result.data) > 0:
            return await OpenAIText2Image.get_image_data(result.data[0].url)
        return ""

    @staticmethod
    async def get_image_data(url):
        """Fetch image data from a URL and encode it as Base64

        :param url: Image url
        :return: Base64-encoded image data.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()  # 如果是 4xx 或 5xx 响应，会引发异常
                    image_data = await response.read()
            return image_data

        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred:{e}")
            return 0


# Export
async def oas3_openai_text_to_image(text, size_type: str = "1024x1024", llm: BaseLLM = None):
    """Text to image

    :param text: The text used for image conversion.
    :param size_type: One of ['256x256', '512x512', '1024x1024']
    :param llm: LLM instance
    :return: The image data is returned in Base64 encoding.
    """
    if not text:
        return ""
    return await OpenAIText2Image(llm).text_2_image(text, size_type=size_type)
