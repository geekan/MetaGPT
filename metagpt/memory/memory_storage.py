#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Desc   : the implement of memory storage
"""

from pathlib import Path
from typing import Optional

from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.faiss import FAISS
from langchain_core.embeddings import Embeddings

from metagpt.const import DATA_PATH, MEM_TTL
from metagpt.document_store.faiss_store import FaissStore
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.utils.serialize import deserialize_message, serialize_message


class MemoryStorage(FaissStore):
    """
    The memory storage with Faiss as ANN search engine
    """

    def __init__(self, mem_ttl: int = MEM_TTL, embedding: Embeddings = None):
        self.role_id: str = None
        self.role_mem_path: str = None
        self.mem_ttl: int = mem_ttl  # later use
        self.threshold: float = 0.1  # experience value. TODO The threshold to filter similar memories
        self._initialized: bool = False

        self.embedding = embedding or OpenAIEmbeddings()
        self.store: FAISS = None  # Faiss engine

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def _load(self) -> Optional["FaissStore"]:
        index_file, store_file = self._get_index_and_store_fname(index_ext=".faiss")  # langchain FAISS using .faiss

        if not (index_file.exists() and store_file.exists()):
            logger.info("Missing at least one of index_file/store_file, load failed and return None")
            return None

        return FAISS.load_local(self.role_mem_path, self.embedding, self.role_id)

    def recover_memory(self, role_id: str) -> list[Message]:
        self.role_id = role_id
        self.role_mem_path = Path(DATA_PATH / f"role_mem/{self.role_id}/")
        self.role_mem_path.mkdir(parents=True, exist_ok=True)

        self.store = self._load()
        messages = []
        if not self.store:
            # TODO init `self.store` under here with raw faiss api instead under `add`
            pass
        else:
            for _id, document in self.store.docstore._dict.items():
                messages.append(deserialize_message(document.metadata.get("message_ser")))
            self._initialized = True

        return messages

    def _get_index_and_store_fname(self, index_ext=".index", pkl_ext=".pkl"):
        if not self.role_mem_path:
            logger.error(f"You should call {self.__class__.__name__}.recover_memory fist when using LongTermMemory")
            return None, None
        index_fpath = Path(self.role_mem_path / f"{self.role_id}{index_ext}")
        storage_fpath = Path(self.role_mem_path / f"{self.role_id}{pkl_ext}")
        return index_fpath, storage_fpath

    def persist(self):
        self.store.save_local(self.role_mem_path, self.role_id)
        logger.debug(f"Agent {self.role_id} persist memory into local")

    def add(self, message: Message) -> bool:
        """add message into memory storage"""
        docs = [message.content]
        metadatas = [{"message_ser": serialize_message(message)}]
        if not self.store:
            # init Faiss
            self.store = self._write(docs, metadatas)
            self._initialized = True
        else:
            self.store.add_texts(texts=docs, metadatas=metadatas)
        self.persist()
        logger.info(f"Agent {self.role_id}'s memory_storage add a message")

    def search_dissimilar(self, message: Message, k=4) -> list[Message]:
        """search for dissimilar messages"""
        if not self.store:
            return []

        resp = self.store.similarity_search_with_score(query=message.content, k=k)
        # filter the result which score is smaller than the threshold
        filtered_resp = []
        for item, score in resp:
            # the smaller score means more similar relation
            if score < self.threshold:
                continue
            # convert search result into Memory
            metadata = item.metadata
            new_mem = deserialize_message(metadata.get("message_ser"))
            filtered_resp.append(new_mem)
        return filtered_resp

    def clean(self):
        index_fpath, storage_fpath = self._get_index_and_store_fname()
        if index_fpath and index_fpath.exists():
            index_fpath.unlink(missing_ok=True)
        if storage_fpath and storage_fpath.exists():
            storage_fpath.unlink(missing_ok=True)

        self.store = None
        self._initialized = False
