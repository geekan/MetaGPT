#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/25 10:20
@Author  : alexanderwu
@File    : faiss_store.py
"""
import asyncio
from pathlib import Path
from typing import Optional

from langchain.vectorstores import FAISS
from langchain_core.embeddings import Embeddings

from metagpt.document import IndexableDocument
from metagpt.document_store.base_store import LocalStore
from metagpt.logs import logger
from metagpt.utils.embedding import get_embedding


class FaissStore(LocalStore):
    def __init__(
        self, raw_data: Path, cache_dir=None, meta_col="source", content_col="output", embedding: Embeddings = None
    ):
        self.meta_col = meta_col
        self.content_col = content_col
        self.embedding = embedding or get_embedding()
        super().__init__(raw_data, cache_dir)

    def _load(self) -> Optional["FaissStore"]:
        index_file, store_file = self._get_index_and_store_fname(index_ext=".faiss")  # langchain FAISS using .faiss

        if not (index_file.exists() and store_file.exists()):
            logger.info("Missing at least one of index_file/store_file, load failed and return None")
            return None

        return FAISS.load_local(self.raw_data_path.parent, self.embedding, self.fname)

    def _write(self, docs, metadatas):
        store = FAISS.from_texts(docs, self.embedding, metadatas=metadatas)
        return store

    def persist(self):
        self.store.save_local(self.raw_data_path.parent, self.fname)

    def search(self, query, expand_cols=False, sep="\n", *args, k=5, **kwargs):
        rsp = self.store.similarity_search(query, k=k, **kwargs)
        logger.debug(rsp)
        if expand_cols:
            return str(sep.join([f"{x.page_content}: {x.metadata}" for x in rsp]))
        else:
            return str(sep.join([f"{x.page_content}" for x in rsp]))

    async def asearch(self, *args, **kwargs):
        return await asyncio.to_thread(self.search, *args, **kwargs)

    def write(self):
        """Initialize the index and library based on the Document (JSON / XLSX, etc.) file provided by the user."""
        if not self.raw_data_path.exists():
            raise FileNotFoundError
        doc = IndexableDocument.from_path(self.raw_data_path, self.content_col, self.meta_col)
        docs, metadatas = doc.get_docs_and_metadatas()

        self.store = self._write(docs, metadatas)
        self.persist()
        return self.store

    def add(self, texts: list[str], *args, **kwargs) -> list[str]:
        """FIXME: Currently, the store is not updated after adding."""
        return self.store.add_texts(texts)

    def delete(self, *args, **kwargs):
        """Currently, langchain does not provide a delete interface."""
        raise NotImplementedError
