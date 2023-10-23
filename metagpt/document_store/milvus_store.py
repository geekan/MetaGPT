#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/28 00:00
@Author  : alexanderwu
@File    : milvus_store.py
"""
from typing import TypedDict

import numpy as np
from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections

from metagpt.document_store.base_store import BaseStore

type_mapping = {
    int: DataType.INT64,
    str: DataType.VARCHAR,
    float: DataType.DOUBLE,
    np.ndarray: DataType.FLOAT_VECTOR
}


def columns_to_milvus_schema(columns: dict, primary_col_name: str = "", desc: str = ""):
    """Assume the structure of columns is str: regular type"""
    fields = []
    for col, ctype in columns.items():
        if ctype == str:
            mcol = FieldSchema(name=col, dtype=type_mapping[ctype], max_length=100)
        elif ctype == np.ndarray:
            mcol = FieldSchema(name=col, dtype=type_mapping[ctype], dim=2)
        else:
            mcol = FieldSchema(name=col, dtype=type_mapping[ctype], is_primary=(col == primary_col_name))
        fields.append(mcol)
    schema = CollectionSchema(fields, description=desc)
    return schema


class MilvusConnection(TypedDict):
    alias: str
    host: str
    port: str


class MilvusStore(BaseStore):
    """
    FIXME: ADD TESTS
    https://milvus.io/docs/v2.0.x/create_collection.md
    """

    def __init__(self, connection):
        connections.connect(**connection)
        self.collection = None

    def _create_collection(self, name, schema):
        collection = Collection(
            name=name,
            schema=schema,
            using='default',
            shards_num=2,
            consistency_level="Strong"
        )
        return collection

    def create_collection(self, name, columns):
        schema = columns_to_milvus_schema(columns, 'idx')
        self.collection = self._create_collection(name, schema)
        return self.collection

    def drop(self, name):
        Collection(name).drop()

    def load_collection(self):
        self.collection.load()

    def build_index(self, field='emb'):
        self.collection.create_index(field, {"index_type": "FLAT", "metric_type": "L2", "params": {}})

    def search(self, query: list[list[float]], *args, **kwargs):
        """
        FIXME: ADD TESTS
        https://milvus.io/docs/v2.0.x/search.md
        All search and query operations within Milvus are executed in memory. Load the collection to memory before conducting a vector similarity search.
        Note the above description, is this logic serious? This should take a long time, right?
        """
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        results = self.collection.search(
            data=query,
            anns_field=kwargs.get('field', 'emb'),
            param=search_params,
            limit=10,
            expr=None,
            consistency_level="Strong"
        )
        # FIXME: results contain id, but to get the actual value from the id, we still need to call the query interface
        return results

    def write(self, name, schema, *args, **kwargs):
        """
        FIXME: ADD TESTS
        https://milvus.io/docs/v2.0.x/create_collection.md
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError

    def add(self, data, *args, **kwargs):
        """
        FIXME: ADD TESTS
        https://milvus.io/docs/v2.0.x/insert_data.md
        import random
        data = [
          [i for i in range(2000)],
          [i for i in range(10000, 12000)],
          [[random.random() for _ in range(2)] for _ in range(2000)],
        ]

        :param args:
        :param kwargs:
        :return:
        """
        self.collection.insert(data)
