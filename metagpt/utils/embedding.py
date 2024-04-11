#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4 20:58
@Author  : alexanderwu
@File    : embedding.py
"""
from llama_index.embeddings.openai import OpenAIEmbedding

from metagpt.config2 import config


def get_embedding() -> OpenAIEmbedding:
    llm = config.get_openai_llm()
    if llm is None:
        raise ValueError("To use OpenAIEmbedding, please ensure that config.llm.api_type is correctly set to 'openai'.")

    embedding = OpenAIEmbedding(api_key=llm.api_key, api_base=llm.base_url)
    return embedding
