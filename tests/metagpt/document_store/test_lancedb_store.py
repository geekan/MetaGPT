#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/9 15:42
@Author  : unkn-wn (Leon Yee)
@File    : test_lancedb_store.py
"""
import random

from metagpt.document_store.lancedb_store import LanceStore


def test_lance_store():
    # This simply establishes the connection to the database, so we can drop the table if it exists
    store = LanceStore("test")

    store.drop("test")

    store.write(
        data=[[random.random() for _ in range(100)] for _ in range(2)],
        metadatas=[{"source": "google-docs"}, {"source": "notion"}],
        ids=["doc1", "doc2"],
    )

    store.add(data=[random.random() for _ in range(100)], metadata={"source": "notion"}, _id="doc3")

    result = store.search([random.random() for _ in range(100)], n_results=3)
    assert len(result) == 3

    store.delete("doc2")
    result = store.search(
        [random.random() for _ in range(100)], n_results=3, where="source = 'notion'", metric="cosine"
    )
    assert len(result) == 1
