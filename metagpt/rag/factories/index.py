"""RAG Index Factory."""

import chromadb
from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.indices.base import BaseIndex
from llama_index.vector_stores.faiss import FaissVectorStore

from metagpt.rag.factories.base import ConfigBasedFactory
from metagpt.rag.schema import (
    BaseIndexConfig,
    BM25IndexConfig,
    ChromaIndexConfig,
    FAISSIndexConfig,
)
from metagpt.rag.vector_stores.chroma import ChromaVectorStore


class RAGIndexFactory(ConfigBasedFactory):
    def __init__(self):
        creators = {
            FAISSIndexConfig: self._create_faiss,
            ChromaIndexConfig: self._create_chroma,
            BM25IndexConfig: self._create_bm25,
        }
        super().__init__(creators)

    def get_index(self, config: BaseIndexConfig, **kwargs) -> BaseIndex:
        """Key is PersistType."""
        return super().get_instance(config, **kwargs)

    def _extract_embed_model(self, config, **kwargs) -> BaseEmbedding:
        return self._val_from_config_or_kwargs("embed_model", config, **kwargs)

    def _create_faiss(self, config: FAISSIndexConfig, **kwargs) -> VectorStoreIndex:
        embed_model = self._extract_embed_model(config, **kwargs)

        vector_store = FaissVectorStore.from_persist_dir(str(config.persist_path))
        storage_context = StorageContext.from_defaults(vector_store=vector_store, persist_dir=config.persist_path)
        index = load_index_from_storage(storage_context=storage_context, embed_model=embed_model)
        return index

    def _create_chroma(self, config: ChromaIndexConfig, **kwargs) -> VectorStoreIndex:
        embed_model = self._extract_embed_model(config, **kwargs)

        db = chromadb.PersistentClient(str(config.persist_path))
        chroma_collection = db.get_or_create_collection(config.collection_name)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        index = VectorStoreIndex.from_vector_store(
            vector_store,
            embed_model=embed_model,
        )
        return index

    def _create_bm25(self, config: BM25IndexConfig, **kwargs) -> VectorStoreIndex:
        embed_model = self._extract_embed_model(config, **kwargs)

        storage_context = StorageContext.from_defaults(persist_dir=config.persist_path)
        index = load_index_from_storage(storage_context=storage_context, embed_model=embed_model)
        return index


get_index = RAGIndexFactory().get_index
