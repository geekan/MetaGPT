#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/8/18
# @Author  : mashenquan
# @File    : openai_text_to_embedding.py
# @Desc    : OpenAI Text-to-Embedding OAS3 api, which provides text-to-embedding functionality.
#             For more details, checkout: `https://platform.openai.com/docs/api-reference/embeddings/object`

from typing import List

import aiohttp
import requests
from pydantic import BaseModel, Field

from metagpt.logs import logger


class Embedding(BaseModel):
    """Represents an embedding vector returned by embedding endpoint.

    Attributes:
        object: A string representing the type of the object.
        embedding: A list of floats representing the embedding vector.
        index: An integer representing the index of the embedding.
    """

    object: str  # The object type, which is always "embedding".
    embedding: List[
        float
    ]  # The embedding vector, which is a list of floats. The length of vector depends on the model as listed in the embedding guide.
    index: int  # The index of the embedding in the list of embeddings.


class Usage(BaseModel):
    """Represents the usage information of the embedding process.

    Attributes:
        prompt_tokens: The number of tokens used in the prompt.
        total_tokens: The total number of tokens used.
    """

    prompt_tokens: int = 0
    total_tokens: int = 0


class ResultEmbedding(BaseModel):
    """Represents the result of the embedding process.

    Attributes:
        object_: A string representing the type of the object. Alias for 'object'.
        data: A list of Embedding objects.
        model: The model used for generating embeddings.
        usage: A Usage object representing the usage information.
    """

    class Config:
        alias = {"object_": "object"}

    object_: str = ""
    data: List[Embedding] = []
    model: str = ""
    usage: Usage = Field(default_factory=Usage)


class OpenAIText2Embedding:
    """Handles the conversion of text to embedding using OpenAI's API."""

    def __init__(self, api_key: str, proxy: str):
        """Initializes the OpenAIText2Embedding with API key and proxy.

        Args:
            api_key: The API key for OpenAI.
            proxy: The proxy address to use for the requests.
        """
        self.api_key = api_key
        self.proxy = proxy

    async def text_2_embedding(self, text, model="text-embedding-ada-002"):
        """Converts text to embedding using the specified model.

        Args:
            text: The text to convert to embedding.
            model: The model ID to use for embedding. Defaults to 'text-embedding-ada-002'.

        Returns:
            A ResultEmbedding object with the embedding result.
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
    """Converts text to embedding using OpenAI's API.

    Args:
        text: The text to convert to embedding.
        openai_api_key: The API key for OpenAI.
        model: The model ID to use for embedding. Defaults to 'text-embedding-ada-002'.
        proxy: The proxy address to use for the requests.

    Returns:
        A ResultEmbedding object with the embedding result if successful, otherwise an empty string.
    """
    if not text:
        return ""
    return await OpenAIText2Embedding(api_key=openai_api_key, proxy=proxy).text_2_embedding(text, model=model)
