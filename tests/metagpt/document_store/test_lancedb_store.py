#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/9 15:42
@Author  : unkn-wn (Leon Yee)
@File    : test_lancedb_store.py
"""
from metagpt.document_store.lancedb_store import LanceStore
import random

def test_lance_store():

    # This simply establishes the connection to the database, so we can drop the table if it exists
    store = LanceStore('test')

    store.drop('test')

    store.create_table(['vector', 'id', 'meta', 'meta2'])

    store.write(data=[[random.random() for _ in range(100)] for _ in range(2)],
            metadatas=[{"source": "google-docs"}, {"source": "notion"}],
            ids=["doc1", "doc2"])

    store.add(data=[random.random() for _ in range(100)], metadatas={"source": "notion"}, ids="doc3")

    result = store.search([random.random() for _ in range(100)], n_results=3)
    print(result)
    assert(len(result) > 0)
