#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/29 14:46
@Author  : alexanderwu
@File    : chromadb_store.py
"""
import chromadb


class ChromaStore:
    """If inherited from BaseStore, or importing other modules from metagpt, a Python exception occurs, which is strange."""

    def __init__(self, name):
        client = chromadb.Client()
        collection = client.create_collection(name)
        self.client = client
        self.collection = collection

    def search(self, query, n_results=2, metadata_filter=None, document_filter=None):
        # kwargs can be used for optional filtering
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=metadata_filter,  # optional filter
            where_document=document_filter,  # optional filter
        )
        return results

    def persist(self):
        """Chroma recommends using server mode and not persisting locally."""
        raise NotImplementedError

    def write(self, documents, metadatas, ids):
        # This function is similar to add(), but it's for more generalized updates
        # It assumes you're passing in lists of docs, metadatas, and ids
        return self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

    def add(self, document, metadata, _id):
        # This function is for adding individual documents
        # It assumes you're passing in a single doc, metadata, and id
        return self.collection.add(
            documents=[document],
            metadatas=[metadata],
            ids=[_id],
        )

    def delete(self, _id):
        return self.collection.delete([_id])
