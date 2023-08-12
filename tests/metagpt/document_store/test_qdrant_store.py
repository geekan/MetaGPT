#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/6/11 21:08
@Author  : alexanderwu
@File    : test_milvus_store.py
"""
import random

from qdrant_client.models import PointStruct, Distance, VectorParams, FieldCondition, Range, Filter

from metagpt.document_store.qdrant_store import QdrantConnection, QdrantStore
from metagpt.logs import logger

vectors = [[random.random() for _ in range(2)] for _ in range(10)]

points = [
    PointStruct(
        id=idx,
        vector=vector,
        payload={"color": "red", "rand_number": idx % 10}
    )
    for idx, vector in enumerate(vectors)
]


def test_milvus_store():
    qdrant_connection = QdrantConnection(memory=True)
    vectors_config = VectorParams(size=2, distance=Distance.COSINE)
    qdrant_store = QdrantStore(qdrant_connection)
    qdrant_store.create_collection("Book", vectors_config, force_recreate=True)
    qdrant_store.delete_collection('Book')
    qdrant_store.create_collection('Book', vectors_config)
    qdrant_store.add("Book", points)
    results = qdrant_store.search("Book", query=[1.0, 1.0])
    logger.info(results)
    assert results
    results = qdrant_store.search("Book", query=[1.0, 1.0], query_filter=Filter(
        must=[
            FieldCondition(
                key='rand_number',
                range=Range(
                    gte=3
                )
            )
        ]
    ))
    logger.info(results)
    assert results
