#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/9 15:42
@Author  : unkn-wn (Leon Yee)
@File    : lancedb_store.py
"""
import os
import shutil

import lancedb


class LanceStore:
    def __init__(self, name):
        db = lancedb.connect("./data/lancedb")
        self.db = db
        self.name = name
        self.table = None

    def search(self, query, n_results=2, metric="L2", nprobes=20, **kwargs):
        # This assumes query is a vector embedding
        # kwargs can be used for optional filtering
        # .select - only searches the specified columns
        # .where - SQL syntax filtering for metadata (e.g. where("price > 100"))
        # .metric - specifies the distance metric to use
        # .nprobes - values will yield better recall (more likely to find vectors if they exist) at the expense of latency.
        if self.table is None:
            raise Exception("Table not created yet, please add data first.")

        results = (
            self.table.search(query)
            .limit(n_results)
            .select(kwargs.get("select"))
            .where(kwargs.get("where"))
            .metric(metric)
            .nprobes(nprobes)
            .to_df()
        )
        return results

    def persist(self):
        raise NotImplementedError

    def write(self, data, metadatas, ids):
        # This function is similar to add(), but it's for more generalized updates
        # "data" is the list of embeddings
        # Inserts into table by expanding metadatas into a dataframe: [{'vector', 'id', 'meta', 'meta2'}, ...]

        documents = []
        for i in range(len(data)):
            row = {"vector": data[i], "id": ids[i]}
            row.update(metadatas[i])
            documents.append(row)

        if self.table is not None:
            self.table.add(documents)
        else:
            self.table = self.db.create_table(self.name, documents)

    def add(self, data, metadata, _id):
        # This function is for adding individual documents
        # It assumes you're passing in a single vector embedding, metadata, and id

        row = {"vector": data, "id": _id}
        row.update(metadata)

        if self.table is not None:
            self.table.add([row])
        else:
            self.table = self.db.create_table(self.name, [row])

    def delete(self, _id):
        # This function deletes a row by id.
        # LanceDB delete syntax uses SQL syntax, so you can use "in" or "="
        if self.table is None:
            raise Exception("Table not created yet, please add data first")

        if isinstance(_id, str):
            return self.table.delete(f"id = '{_id}'")
        else:
            return self.table.delete(f"id = {_id}")

    def drop(self, name):
        # This function drops a table, if it exists.

        path = os.path.join(self.db.uri, name + ".lance")
        if os.path.exists(path):
            shutil.rmtree(path)
