#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4 20:58
@Author  : alexanderwu
@File    : embedding.py
"""
from langchain_community.embeddings import OpenAIEmbeddings

from metagpt.config2 import config


def get_embedding():
    llm = config.get_openai_llm()
    embedding = OpenAIEmbeddings(openai_api_key=llm.api_key, openai_api_base=llm.base_url)
    return embedding
