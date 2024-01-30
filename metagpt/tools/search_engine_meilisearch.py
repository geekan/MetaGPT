#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/5/22 21:33
# @Author  : alexanderwu
# @File    : search_engine_meilisearch.py


from typing import List

import meilisearch
from meilisearch.index import Index

from metagpt.utils.exceptions import handle_exception


class DataSource:
    """Represents a data source with a name and a URL.

    Args:
        name: The name of the data source.
        url: The URL of the data source.

    Attributes:
        name: The name of the data source.
        url: The URL of the data source.
    """

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url


class MeilisearchEngine:
    """Engine for interacting with a Meilisearch instance.

    This class provides methods to set an index, add documents to an index, and search within an index.

    Args:
        url: The URL of the Meilisearch instance.
        token: The token used for authentication with the Meilisearch instance.

    Attributes:
        client: The Meilisearch client instance.
        _index: The current Meilisearch index being interacted with.
    """

    def __init__(self, url, token):
        self.client = meilisearch.Client(url, token)
        self._index: Index = None

    def set_index(self, index):
        """Sets the current index to the specified index.

        Args:
            index: The index to be set as the current index.
        """
        self._index = index

    def add_documents(self, data_source: DataSource, documents: List[dict]):
        """Adds documents to an index associated with a data source.

        If the index does not exist, it is created. The index name is derived from the data source name.

        Args:
            data_source: The data source associated with the documents.
            documents: A list of documents to be added to the index.
        """
        index_name = f"{data_source.name}_index"
        if index_name not in self.client.get_indexes():
            self.client.create_index(uid=index_name, options={"primaryKey": "id"})
        index = self.client.get_index(index_name)
        index.add_documents(documents)
        self.set_index(index)

    @handle_exception(exception_type=Exception, default_return=[])
    def search(self, query):
        """Searches the current index with the given query.

        Args:
            query: The search query.

        Returns:
            A list of search hits.
        """
        search_results = self._index.search(query)
        return search_results["hits"]
