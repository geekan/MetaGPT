#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18
@Author  : mashenquan
@File    : openai_text_to_embedding.py
@Desc    : OpenAI Text-to-Embedding OAS3 api, which provides text-to-embedding functionality.
            For more details, checkout: `https://platform.openai.com/docs/api-reference/embeddings/object`
"""
from typing import List

import aiohttp
import requests
from pydantic import BaseModel, Field

from metagpt.logs import logger


class Embedding(BaseModel):
    """Represents an embedding vector returned by embedding endpoint."""

    object: str  # The object type, which is always "embedding".
    embedding: List[
        float
    ]  # The embedding vector, which is a list of floats. The length of vector depends on the model as listed in the embedding guide.
    index: int  # The index of the embedding in the list of embeddings.


class Usage(BaseModel):
    prompt_tokens: int = 0
    total_tokens: int = 0


class ResultEmbedding(BaseModel):
    class Config:
        alias = {"object_": "object"}

    object_: str = ""
    data: List[Embedding] = []
    model: str = ""
    usage: Usage = Field(default_factory=Usage)


class OpenAIText2Embedding:
    def __init__(self, api_key: str, proxy: str):
        """
        :param openai_api_key: OpenAI API key, For more details, checkout: `https://platform.openai.com/account/api-keys`
        """
        self.api_key = api_key
        self.proxy = proxy

    async def text_2_embedding(self, text, model="text-embedding-ada-002"):
        """Text to embedding

        :param text: The text used for embedding.
        :param model: One of ['text-embedding-ada-002'], ID of the model to use. For more details, checkout: `https://api.openai.com/v1/models`.
        :return: A json object of :class:`ResultEmbedding` class if successful, otherwise `{}`.
        """

        proxies = {"proxy": self.proxy} if self.proxy else {}
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        data = {"input": text, "model": model}
        url = "https://api.openai.com/v1/embeddings"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, **proxies) as response:
                    data = await response.json()
                    return ResultEmbedding(**data)
        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred:{e}")
        return ResultEmbedding()


# Export
async def oas3_openai_text_to_embedding(text, openai_api_key: str, model="text-embedding-ada-002", proxy: str = ""):
    """Text to embedding

    :param text: The text used for embedding.
    :param model: One of ['text-embedding-ada-002'], ID of the model to use. For more details, checkout: `https://api.openai.com/v1/models`.
    :param config: OpenAI config with API key, For more details, checkout: `https://platform.openai.com/account/api-keys`
    :return: A json object of :class:`ResultEmbedding` class if successful, otherwise `{}`.
    """
    if not text:
        return ""
    return await OpenAIText2Embedding(api_key=openai_api_key, proxy=proxy).text_2_embedding(text, model=model)
