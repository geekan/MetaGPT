#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18
@Author  : mashenquan
@File    : text_to_image.py
@Desc    : Text-to-Image skill, which provides text-to-image functionality.
"""

from metagpt.tools.openai_text_2_image import oas3_openai_text_2_image
from metagpt.utils.common import initialize_environment


def text_to_image(text, size_type: str = "1024x1024", openai_api_key=""):
    """Text to image

    :param text: The text used for image conversion.
    :param openai_api_key: OpenAI API key, For more details, checkout: `https://platform.openai.com/account/api-keys`
    :param size_type: One of ['256x256', '512x512', '1024x1024']
    :return: The image data is returned in Base64 encoding.
    """
    initialize_environment()
    return oas3_openai_text_2_image(text, size_type, openai_api_key)
