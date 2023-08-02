#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/22 21:33
@Author  : alexanderwu
@File    : search_engine_meilisearch.py
"""

from typing import List

import meilisearch
from meilisearch.index import Index


class DataSource:
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url


class MeilisearchEngine:
    def __init__(self, url, token):
        self.client = meilisearch.Client(url, token)
        self._index: Index = None

    def set_index(self, index):
        self._index = index

    def add_documents(self, data_source: DataSource, documents: List[dict]):
        index_name = f"{data_source.name}_index"
        if index_name not in self.client.get_indexes():
            self.client.create_index(uid=index_name, options={'primaryKey': 'id'})
        index = self.client.get_index(index_name)
        index.add_documents(documents)
        self.set_index(index)

    def search(self, query):
        try:
            search_results = self._index.search(query)
            return search_results['hits']
        except Exception as e:
            # Handle MeiliSearch API errors
            print(f"MeiliSearch API error: {e}")
            return []
