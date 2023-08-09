#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/9 15:42
@Author  : unkn-wn (Leon Yee)
@File    : lancedb_store.py
"""
import lancedb
import pyarrow as pa
import pandas as pd


class LanceStore:
    def __init__(self, name):
        db = lancedb.connect('./data/lancedb')
        self.db = db
        self.name = name
        self.table = None

    def create_table(self, columns: list):
        # Create table given the columns as a list.
        df = pd.DataFrame(columns=columns)
        schema = pa.Schema.from_pandas(df)
        schema = schema.remove_metadata()
        schema = schema.remove(len(schema) - 1)

        self.table = self.db.create_table(self.name, schema)

    def search(self, query, n_results=2, metric="L2", nprobes=20, **kwargs):
        # This assumes query is a vector embedding
        # kwargs can be used for optional filtering
        # .select - only searches the specified columns
        # .where - SQL syntax filtering for metadata (e.g. where("price > 100"))
        # .metric - specifies the distance metric to use
        # .nprobes - values will yield better recall (more likely to find vectors if they exist) at the expense of latency.
        results = self.table \
            .search(query) \
            .limit(n_results) \
            .select(kwargs.get('select')) \
            .where(kwargs.get('where')) \
            .metric(metric) \
            .nprobes(nprobes) \
            .to_df()
        return results

    def persist(self):
        raise NotImplementedError

    def write(self, data, metadatas, ids):
        # This function is similar to add(), but it's for more generalized updates
        # "data" is the list of embeddings
        # Inserts into table by expanding metadatas into a dataframe: [{'vector', 'id', 'meta', 'meta2'}, ...]
        if self.table == None: raise Exception("Table not created yet, please use create_table([columns]) first")

        documents = []
        for i in range(len(data)):
            row = {
                'vector': data[i],
                'id': ids[i]
            }
            row.update(metadatas[i])
            documents.append(row)

        return self.table.add(documents)

    def add(self, data, metadata, _id):
        # This function is for adding individual documents
        # It assumes you're passing in a single vector embedding, metadata, and id
        if self.table == None: raise Exception("Table not created yet, please use create_table([columns]) first")

        row = {
            'vector': data,
            'id': _id
        }
        row.update(metadata)

        return self.table.add([row])

    def delete(self, _id):
        # This function deletes a row by id.
        # LanceDB delete syntax uses SQL syntax, so you can use "in" or "="
        if self.table == None: raise Exception("Table not created yet, please use create_table([columns]) first")

        if isinstance(_id, str):
            return self.table.delete(f"id = '{_id}'")
        else:
            return self.table.delete(f"id = {_id}")
