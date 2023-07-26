#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/6/11 21:08
@Author  : alexanderwu
@File    : test_milvus_store.py
"""
import random

import numpy as np

from metagpt.document_store.milvus_store import MilvusConnection, MilvusStore
from metagpt.logs import logger

book_columns = {'idx': int, 'name': str, 'desc': str, 'emb': np.ndarray, 'price': float}
book_data = [
    [i for i in range(10)],
    [f"book-{i}" for i in range(10)],
    [f"book-desc-{i}" for i in range(10000, 10010)],
    [[random.random() for _ in range(2)] for _ in range(10)],
    [random.random() for _ in range(10)],
]


def test_milvus_store():
    milvus_connection = MilvusConnection(alias="default", host="192.168.50.161", port="30530")
    milvus_store = MilvusStore(milvus_connection)
    milvus_store.drop('Book')
    milvus_store.create_collection('Book', book_columns)
    milvus_store.add(book_data)
    milvus_store.build_index('emb')
    milvus_store.load_collection()

    results = milvus_store.search([[1.0, 1.0]], field='emb')
    logger.info(results)
    assert results
