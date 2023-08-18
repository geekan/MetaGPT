#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18
@Author  : mashenquan
@File    : text_to_image.py
@Desc    : Text-to-Image skill, which provides text-to-image functionality.
"""
import os

from metagpt.tools.metagpt_text_to_image import oas3_metagpt_text_to_image
from metagpt.tools.openai_text_to_image import oas3_openai_text_to_image
from metagpt.utils.common import initialize_environment


def text_to_image(text, size_type: str = "512x512", openai_api_key="", model_url=""):
    """Text to image

    :param text: The text used for image conversion.
    :param openai_api_key: OpenAI API key, For more details, checkout: `https://platform.openai.com/account/api-keys`
    :param size_type: If using OPENAI, the available size options are ['256x256', '512x512', '1024x1024'], while for MetaGPT, the options are ['512x512', '512x768'].
    :param model_url: MetaGPT model url
    :return: The image data is returned in Base64 encoding.
    """
    initialize_environment()
    if os.environ.get("METAGPT_TEXT_TO_IMAGE_MODEL") or model_url:
        return oas3_metagpt_text_to_image(text, size_type, model_url)
    if os.environ.get("OPENAI_API_KEY") or openai_api_key:
        return oas3_openai_text_to_image(text, size_type, openai_api_key)
    raise EnvironmentError
