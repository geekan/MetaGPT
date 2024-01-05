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
    PointStruct(id=idx, vector=vector, payload={"color": "red", "rand_number": idx % 10})
    for idx, vector in enumerate(vectors)
]


def assert_almost_equal(actual, expected):
    delta = 1e-10
    if isinstance(expected, list):
        assert len(actual) == len(expected)
        for ac, exp in zip(actual, expected):
            assert abs(ac - exp) <= delta, f"{ac} is not within {delta} of {exp}"
    else:
        assert abs(actual - expected) <= delta, f"{actual} is not within {delta} of {expected}"


def test_qdrant_store():
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
    assert results[0]["id"] == 2
    assert_almost_equal(results[0]["score"], 0.999106722578389)
    assert results[1]["id"] == 7
    assert_almost_equal(results[1]["score"], 0.9961650411397226)
    results = qdrant_store.search("Book", query=[1.0, 1.0], return_vector=True)
    assert results[0]["id"] == 2
    assert_almost_equal(results[0]["score"], 0.999106722578389)
    assert_almost_equal(results[0]["vector"], [0.7363563179969788, 0.6765939593315125])
    assert results[1]["id"] == 7
    assert_almost_equal(results[1]["score"], 0.9961650411397226)
    assert_almost_equal(results[1]["vector"], [0.7662628889083862, 0.6425272226333618])
    results = qdrant_store.search(
        "Book",
        query=[1.0, 1.0],
        query_filter=Filter(must=[FieldCondition(key="rand_number", range=Range(gte=8))]),
    )
    assert results[0]["id"] == 8
    assert_almost_equal(results[0]["score"], 0.9100373450784073)
    assert results[1]["id"] == 9
    assert_almost_equal(results[1]["score"], 0.7127610621127889)
    results = qdrant_store.search(
        "Book",
        query=[1.0, 1.0],
        query_filter=Filter(must=[FieldCondition(key="rand_number", range=Range(gte=8))]),
        return_vector=True,
    )
    assert_almost_equal(results[0]["vector"], [0.35037919878959656, 0.9366079568862915])
    assert_almost_equal(results[1]["vector"], [0.9999677538871765, 0.00802854634821415])
