#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18
@Author  : mashenquan
@File    : text_to_image.py
@Desc    : Text-to-Image skill, which provides text-to-image functionality.
"""

from metagpt.config import CONFIG
from metagpt.tools.metagpt_text_to_image import oas3_metagpt_text_to_image
from metagpt.tools.openai_text_to_image import oas3_openai_text_to_image


async def text_to_image(text, size_type: str = "512x512", openai_api_key="", model_url="", **kwargs):
    """Text to image

    :param text: The text used for image conversion.
    :param openai_api_key: OpenAI API key, For more details, checkout: `https://platform.openai.com/account/api-keys`
    :param size_type: If using OPENAI, the available size options are ['256x256', '512x512', '1024x1024'], while for MetaGPT, the options are ['512x512', '512x768'].
    :param model_url: MetaGPT model url
    :return: The image data is returned in Base64 encoding.
    """
    image_declaration = "data:image/png;base64,"
    if CONFIG.METAGPT_TEXT_TO_IMAGE_MODEL_URL or model_url:
        data = await oas3_metagpt_text_to_image(text, size_type, model_url)
        return image_declaration + data if data else ""

    if CONFIG.OPENAI_API_KEY or openai_api_key:
        data = await oas3_openai_text_to_image(text, size_type, openai_api_key)
        return image_declaration + data if data else ""

    raise EnvironmentError


