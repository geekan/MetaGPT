#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/6/11 21:08
@Author  : hezhaozhao
@File    : test_qdrant_store.py
"""
import random

from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    PointStruct,
    Range,
    VectorParams,
)

from metagpt.document_store.qdrant_store import QdrantConnection, QdrantStore

seed_value = 42
random.seed(seed_value)

vectors = [[random.random() for _ in range(2)] for _ in range(10)]

points = [
    PointStruct(
        id=idx, vector=vector, payload={"color": "red", "rand_number": idx % 10}
    )
    for idx, vector in enumerate(vectors)
]


def test_milvus_store():
    qdrant_connection = QdrantConnection(memory=True)
    vectors_config = VectorParams(size=2, distance=Distance.COSINE)
    qdrant_store = QdrantStore(qdrant_connection)
    qdrant_store.create_collection("Book", vectors_config, force_recreate=True)
    assert qdrant_store.has_collection("Book") is True
    qdrant_store.delete_collection("Book")
    assert qdrant_store.has_collection("Book") is False
    qdrant_store.create_collection("Book", vectors_config)
    assert qdrant_store.has_collection("Book") is True
    qdrant_store.add("Book", points)
    results = qdrant_store.search("Book", query=[1.0, 1.0])
    assert results == [
        {
            "id": 2,
            "version": 0,
            "score": 0.999106722578389,
            "payload": {"color": "red", "rand_number": 2},
            "vector": None,
        },
        {
            "id": 7,
            "version": 0,
            "score": 0.9961650411397226,
            "payload": {"color": "red", "rand_number": 7},
            "vector": None,
        },
        {
            "id": 1,
            "version": 0,
            "score": 0.9946351526856256,
            "payload": {"color": "red", "rand_number": 1},
            "vector": None,
        },
        {
            "id": 5,
            "version": 0,
            "score": 0.9297466022881021,
            "payload": {"color": "red", "rand_number": 5},
            "vector": None,
        },
        {
            "id": 8,
            "version": 0,
            "score": 0.9100373450784073,
            "payload": {"color": "red", "rand_number": 8},
            "vector": None,
        },
        {
            "id": 6,
            "version": 0,
            "score": 0.7944306996390111,
            "payload": {"color": "red", "rand_number": 6},
            "vector": None,
        },
        {
            "id": 3,
            "version": 0,
            "score": 0.7723528053480722,
            "payload": {"color": "red", "rand_number": 3},
            "vector": None,
        },
        {
            "id": 4,
            "version": 0,
            "score": 0.755163629383033,
            "payload": {"color": "red", "rand_number": 4},
            "vector": None,
        },
        {
            "id": 0,
            "version": 0,
            "score": 0.73420337995255,
            "payload": {"color": "red", "rand_number": 0},
            "vector": None,
        },
        {
            "id": 9,
            "version": 0,
            "score": 0.7127610621127889,
            "payload": {"color": "red", "rand_number": 9},
            "vector": None,
        },
    ]
    results = qdrant_store.search("Book", query=[1.0, 1.0], return_vector=True)
    assert results == [
        {
            "id": 2,
            "version": 0,
            "score": 0.999106722578389,
            "payload": {"color": "red", "rand_number": 2},
            "vector": [0.7363563179969788, 0.6765939593315125],
        },
        {
            "id": 7,
            "version": 0,
            "score": 0.9961650411397226,
            "payload": {"color": "red", "rand_number": 7},
            "vector": [0.7662628889083862, 0.6425272226333618],
        },
        {
            "id": 1,
            "version": 0,
            "score": 0.9946351526856256,
            "payload": {"color": "red", "rand_number": 1},
            "vector": [0.7764601111412048, 0.6301664113998413],
        },
        {
            "id": 5,
            "version": 0,
            "score": 0.9297466022881021,
            "payload": {"color": "red", "rand_number": 5},
            "vector": [0.39707326889038086, 0.9177868962287903],
        },
        {
            "id": 8,
            "version": 0,
            "score": 0.9100373450784073,
            "payload": {"color": "red", "rand_number": 8},
            "vector": [0.35037919878959656, 0.9366079568862915],
        },
        {
            "id": 6,
            "version": 0,
            "score": 0.7944306996390111,
            "payload": {"color": "red", "rand_number": 6},
            "vector": [0.13228265941143036, 0.991212010383606],
        },
        {
            "id": 3,
            "version": 0,
            "score": 0.7723528053480722,
            "payload": {"color": "red", "rand_number": 3},
            "vector": [0.9952857494354248, 0.0969860628247261],
        },
        {
            "id": 4,
            "version": 0,
            "score": 0.755163629383033,
            "payload": {"color": "red", "rand_number": 4},
            "vector": [0.9975154995918274, 0.07044714689254761],
        },
        {
            "id": 0,
            "version": 0,
            "score": 0.73420337995255,
            "payload": {"color": "red", "rand_number": 0},
            "vector": [0.9992359280586243, 0.03908444941043854],
        },
        {
            "id": 9,
            "version": 0,
            "score": 0.7127610621127889,
            "payload": {"color": "red", "rand_number": 9},
            "vector": [0.9999677538871765, 0.00802854634821415],
        },
    ]
    results = qdrant_store.search(
        "Book",
        query=[1.0, 1.0],
        query_filter=Filter(
            must=[FieldCondition(key="rand_number", range=Range(gte=8))]
        ),
    )
    assert results == [
        {
            "id": 8,
            "version": 0,
            "score": 0.9100373450784073,
            "payload": {"color": "red", "rand_number": 8},
            "vector": None,
        },
        {
            "id": 9,
            "version": 0,
            "score": 0.7127610621127889,
            "payload": {"color": "red", "rand_number": 9},
            "vector": None,
        },
    ]
    results = qdrant_store.search(
        "Book",
        query=[1.0, 1.0],
        query_filter=Filter(
            must=[FieldCondition(key="rand_number", range=Range(gte=8))]
        ),
        return_vector=True,
    )
    assert results == [
        {
            "id": 8,
            "version": 0,
            "score": 0.9100373450784073,
            "payload": {"color": "red", "rand_number": 8},
            "vector": [0.35037919878959656, 0.9366079568862915],
        },
        {
            "id": 9,
            "version": 0,
            "score": 0.7127610621127889,
            "payload": {"color": "red", "rand_number": 9},
            "vector": [0.9999677538871765, 0.00802854634821415],
        },
    ]
