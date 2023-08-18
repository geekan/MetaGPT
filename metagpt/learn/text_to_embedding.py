#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18
@Author  : mashenquan
@File    : text_to_embedding.py
@Desc    : Text-to-Embedding skill, which provides text-to-embedding functionality.
"""

from metagpt.tools.openai_text_2_embedding import oas3_openai_text_2_embedding
from metagpt.utils.common import initialize_environment


def text_to_embedding(text, model="text-embedding-ada-002", openai_api_key=""):
    """Text to embedding

    :param text: The text used for embedding.
    :param model: One of ['text-embedding-ada-002'], ID of the model to use. For more details, checkout: `https://api.openai.com/v1/models`.
    :param openai_api_key: OpenAI API key, For more details, checkout: `https://platform.openai.com/account/api-keys`
    :return: A json object of :class:`ResultEmbedding` class if successful, otherwise `{}`.
    """
    initialize_environment()
    return oas3_openai_text_2_embedding(text, model=model, openai_api_key=openai_api_key)