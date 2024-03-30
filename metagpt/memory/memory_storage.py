#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Desc   : the implement of memory storage
"""
import shutil
from pathlib import Path

from llama_index.core.embeddings import BaseEmbedding

from metagpt.const import DATA_PATH, MEM_TTL
from metagpt.logs import logger
from metagpt.rag.engines.simple import SimpleEngine
from metagpt.rag.schema import FAISSIndexConfig, FAISSRetrieverConfig
from metagpt.schema import Message
from metagpt.utils.embedding import get_embedding


class MemoryStorage(object):
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

        self.faiss_engine = None

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def recover_memory(self, role_id: str) -> list[Message]:
        self.role_id = role_id
        self.role_mem_path = Path(DATA_PATH / f"role_mem/{self.role_id}/")
        self.role_mem_path.mkdir(parents=True, exist_ok=True)
        self.cache_dir = self.role_mem_path

        if self.role_mem_path.joinpath("default__vector_store.json").exists():
            self.faiss_engine = SimpleEngine.from_index(
                index_config=FAISSIndexConfig(persist_path=self.cache_dir),
                retriever_configs=[FAISSRetrieverConfig()],
                embed_model=self.embedding,
            )
        else:
            self.faiss_engine = SimpleEngine.from_objs(
                objs=[], retriever_configs=[FAISSRetrieverConfig()], embed_model=self.embedding
            )
        self._initialized = True

    def add(self, message: Message) -> bool:
        """add message into memory storage"""
        self.faiss_engine.add_objs([message])
        logger.info(f"Role {self.role_id}'s memory_storage add a message")

    async def search_similar(self, message: Message, k=4) -> list[Message]:
        """search for similar messages"""
        # filter the result which score is smaller than the threshold
        filtered_resp = []
        resp = await self.faiss_engine.aretrieve(message.content)
        for item in resp:
            if item.score < self.threshold:
                filtered_resp.append(item.metadata.get("obj"))
        return filtered_resp

    def clean(self):
        shutil.rmtree(self.cache_dir, ignore_errors=True)
        self._initialized = False

    def persist(self):
        if self.faiss_engine:
            self.faiss_engine.retriever._index.storage_context.persist(self.cache_dir)
