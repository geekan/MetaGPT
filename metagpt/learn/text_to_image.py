#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18
@Author  : mashenquan
@File    : text_to_image.py
@Desc    : Text-to-Image skill, which provides text-to-image functionality.
"""
import os

from metagpt.learn.skill_metadata import skill_metadata
from metagpt.tools.metagpt_text_to_image import oas3_metagpt_text_to_image
from metagpt.tools.openai_text_to_image import oas3_openai_text_to_image
from metagpt.utils.common import initialize_environment


@skill_metadata(name="Text to image",
                description="Create a drawing based on the text.",
                requisite="`OPENAI_API_KEY` or `METAGPT_TEXT_TO_IMAGE_MODEL`")
def text_to_image(text, size_type: str = "512x512", openai_api_key="", model_url="", **kwargs):
    """Text to image

    :param text: The text used for image conversion.
    :param openai_api_key: OpenAI API key, For more details, checkout: `https://platform.openai.com/account/api-keys`
    :param size_type: If using OPENAI, the available size options are ['256x256', '512x512', '1024x1024'], while for MetaGPT, the options are ['512x512', '512x768'].
    :param model_url: MetaGPT model url
    :return: The image data is returned in Base64 encoding.
    """
    initialize_environment()
    image_declaration = "data:image/png;base64,"
    if os.environ.get("METAGPT_TEXT_TO_IMAGE_MODEL") or model_url:
        data = oas3_metagpt_text_to_image(text, size_type, model_url)
        return image_declaration + data if data else ""
    if os.environ.get("OPENAI_API_KEY") or openai_api_key:
        data = oas3_openai_text_to_image(text, size_type, openai_api_key)
        return image_declaration + data if data else ""

    raise EnvironmentError


