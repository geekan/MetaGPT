#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Desc   : the implement of memory storage
"""
import shutil
from pathlib import Path

from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.schema import QueryBundle, TextNode

from metagpt.const import DATA_PATH, MEM_TTL
from metagpt.document_store.faiss_store import FaissStore
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.utils.embedding import get_embedding


class MemoryStorage(FaissStore):
    """
    The memory storage with Faiss as ANN search engine
    """

    def __init__(self, mem_ttl: int = MEM_TTL, embedding: BaseEmbedding = None):
        self.role_id: str = None
        self.role_mem_path: str = None
        self.mem_ttl: int = mem_ttl  # later use
        self.threshold: float = 0.1  # experience value. TODO The threshold to filter similar memories
        self._initialized: bool = False
        self.embedding = embedding or get_embedding()

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def recover_memory(self, role_id: str) -> list[Message]:
        self.role_id = role_id
        self.role_mem_path = Path(DATA_PATH / f"role_mem/{self.role_id}/")
        self.role_mem_path.mkdir(parents=True, exist_ok=True)
        self.cache_dir = self.role_mem_path

        self.store = self._load()
        messages = []
        if not self.store:
            # TODO init `self.store` under here with raw faiss api instead under `add`
            pass
        else:
            for _id, document in self.store.docstore._dict.items():
                messages.append(Message(**document.metadata.get("obj_dict")))
            self._initialized = True

        return messages

    def add(self, message: Message) -> bool:
        """add message into memory storage"""
        docs = [message.content]
        metadatas = [{"obj_dict": message.model_dump()}]
        if not self.store:
            # init Faiss
            self.store = self._write(docs, metadatas)
            self._initialized = True
        else:
            text_node = TextNode(text=message.content, metadata=metadatas[0])
            self.store.insert_nodes([text_node])
        self.persist()
        logger.info(f"Agent {self.role_id}'s memory_storage add a message")

    def search_dissimilar(self, message: Message, k=4) -> list[Message]:
        """search for dissimilar messages"""
        if not self.store:
            return []

        retriever = self.store.as_retriever(similarity_top_k=k)
        resp = retriever.retrieve(
            QueryBundle(query_str=message.content, embedding=self.embedding.get_text_embedding(message.content))
        )
        # filter the result which score is smaller than the threshold
        filtered_resp = []
        for item in resp:
            # the smaller score means more similar relation

            if item.score < self.threshold:
                continue
            # convert search result into Memory
            metadata = item.node.metadata
            new_mem = Message(**metadata.get("obj_dict", {}))
            filtered_resp.append(new_mem)
        return filtered_resp

    def clean(self):
        shutil.rmtree(self.cache_dir, ignore_errors=True)

        self.store = None
        self._initialized = False
