#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/27 20:20
@Author  : alexanderwu
@File    : test_faiss_store.py
"""

import numpy as np
import pytest

from metagpt.const import EXAMPLE_PATH
from metagpt.document_store import FaissStore
from metagpt.logs import logger
from metagpt.roles import Sales


def mock_openai_embed_documents(self, texts: list[str], show_progress: bool = False) -> list[list[float]]:
    num = len(texts)
    embeds = np.random.randint(1, 100, size=(num, 1536))  # 1536: openai embedding dim
    embeds = (embeds - embeds.mean(axis=0)) / embeds.std(axis=0)
    return embeds.tolist()


def mock_openai_embed_document(self, text: str) -> list[float]:
    embeds = mock_openai_embed_documents(self, [text])
    return embeds[0]


@pytest.mark.asyncio
async def test_search_json(mocker):
    mocker.patch("llama_index.embeddings.openai.base.OpenAIEmbedding._get_text_embeddings", mock_openai_embed_documents)
    mocker.patch("llama_index.embeddings.openai.base.OpenAIEmbedding._get_text_embedding", mock_openai_embed_document)

    store = FaissStore(EXAMPLE_PATH / "data/search_kb/example.json")
    role = Sales(profile="Sales", store=store)
    query = "Which facial cleanser is good for oily skin?"
    result = await role.run(query)
    logger.info(result)


@pytest.mark.asyncio
async def test_search_xlsx(mocker):
    mocker.patch("llama_index.embeddings.openai.base.OpenAIEmbedding._get_text_embeddings", mock_openai_embed_documents)
    mocker.patch("llama_index.embeddings.openai.base.OpenAIEmbedding._get_text_embedding", mock_openai_embed_document)

    store = FaissStore(EXAMPLE_PATH / "data/search_kb/example.xlsx", meta_col="Answer", content_col="Question")
    role = Sales(profile="Sales", store=store)
    query = "Which facial cleanser is good for oily skin?"
    result = await role.run(query)
    logger.info(result)


@pytest.mark.asyncio
async def test_write(mocker):
    mocker.patch("llama_index.embeddings.openai.base.OpenAIEmbedding._get_text_embeddings", mock_openai_embed_documents)
    mocker.patch("llama_index.embeddings.openai.base.OpenAIEmbedding._get_text_embedding", mock_openai_embed_document)

    store = FaissStore(EXAMPLE_PATH / "data/search_kb/example.xlsx", meta_col="Answer", content_col="Question")
    _faiss_store = store.write()
    assert _faiss_store.storage_context.docstore
    assert _faiss_store.storage_context.vector_store.client
