#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18
@Author  : mashenquan
@File    : text_to_image.py
@Desc    : Text-to-Image skill, which provides text-to-image functionality.
"""
import base64

import metagpt.config2
from metagpt.config2 import Config
from metagpt.const import BASE64_FORMAT
from metagpt.llm import LLM
from metagpt.tools.metagpt_text_to_image import oas3_metagpt_text_to_image
from metagpt.tools.openai_text_to_image import oas3_openai_text_to_image
from metagpt.utils.s3 import S3


async def text_to_image(text, size_type: str = "512x512", config: Config = metagpt.config2.config):
    """Text to image

    :param text: The text used for image conversion.
    :param size_type: If using OPENAI, the available size options are ['256x256', '512x512', '1024x1024'], while for MetaGPT, the options are ['512x512', '512x768'].
    :param config: Config
    :return: The image data is returned in Base64 encoding.
    """
    image_declaration = "data:image/png;base64,"

    model_url = config.metagpt_tti_url
    if model_url:
        binary_data = await oas3_metagpt_text_to_image(text, size_type, model_url)
    elif config.get_openai_llm():
        llm = LLM(llm_config=config.get_openai_llm())
        binary_data = await oas3_openai_text_to_image(text, size_type, llm=llm)
    else:
        raise ValueError("Missing necessary parameters.")
    base64_data = base64.b64encode(binary_data).decode("utf-8")

    s3 = S3(config.s3)
    url = await s3.cache(data=base64_data, file_ext=".png", format=BASE64_FORMAT)
    if url:
        return f"![{text}]({url})"
    return image_declaration + base64_data if base64_data else ""
