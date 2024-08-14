#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18
@Author  : mashenquan
@File    : text_to_embedding.py
@Desc    : Text-to-Embedding skill, which provides text-to-embedding functionality.
"""
from typing import Optional

from metagpt.config2 import Config
from metagpt.tools.openai_text_to_embedding import oas3_openai_text_to_embedding


async def text_to_embedding(text, model="text-embedding-ada-002", config: Optional[Config] = None):
    """Text to embedding

    :param text: The text used for embedding.
    :param model: One of ['text-embedding-ada-002'], ID of the model to use. For more details, checkout: `https://api.openai.com/v1/models`.
    :param config: OpenAI config with API key, For more details, checkout: `https://platform.openai.com/account/api-keys`
    :return: A json object of :class:`ResultEmbedding` class if successful, otherwise `{}`.
    """
    config = config if config else Config.default()
    openai_api_key = config.get_openai_llm().api_key
    proxy = config.get_openai_llm().proxy
    return await oas3_openai_text_to_embedding(text, model=model, openai_api_key=openai_api_key, proxy=proxy)
