"""Retriever Factory"""
import faiss
from llama_index import StorageContext, VectorStoreIndex
from llama_index.indices.base import BaseIndex
from llama_index.vector_stores.faiss import FaissVectorStore

from metagpt.rag.retrievers.base import RAGRetriever
from metagpt.rag.retrievers.bm25_retriever import DynamicBM25Retriever
from metagpt.rag.retrievers.faiss_retriever import FAISSRetriever
from metagpt.rag.retrievers.hybrid_retriever import SimpleHybridRetriever
from metagpt.rag.schema import (
    BM25RetrieverConfig,
    FAISSRetrieverConfig,
    RetrieverConfigType,
)


class RetrieverFactory:
    def __init__(self):
        self.retriever_creators = {
            FAISSRetrieverConfig: self._create_faiss_retriever,
            BM25RetrieverConfig: self._create_bm25_retriever,
        }

    def get_retriever(self, index: BaseIndex, configs: list[RetrieverConfigType] = None) -> RAGRetriever:
        """Creates and returns a retriever instance based on the provided configurations."""
        if not configs:
            return self._default_retriever(index)

        retrievers = [self._get_retriever(index, config) for config in configs]

        return (
            SimpleHybridRetriever(*retrievers, service_context=index.service_context)
            if len(retrievers) > 1
            else retrievers[0]
        )

    def _default_retriever(self, index: BaseIndex) -> RAGRetriever:
        return index.as_retriever()

    def _get_retriever(self, index: BaseIndex, config: RetrieverConfigType) -> RAGRetriever:
        create_func = self.retriever_creators.get(type(config))
        if create_func:
            return create_func(index, config)

        raise ValueError(f"Unknown retriever config: {config}")

    def _create_faiss_retriever(self, index: BaseIndex, config: FAISSRetrieverConfig):
        vector_store = FaissVectorStore(faiss_index=faiss.IndexFlatL2(config.dimensions))
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        vector_index = VectorStoreIndex(
            nodes=list(index.docstore.docs.values()),
            storage_context=storage_context,
            service_context=index.service_context,
        )
        return FAISSRetriever(vector_index, **config.model_dump())

    def _create_bm25_retriever(self, index: BaseIndex, config: BM25RetrieverConfig):
        return DynamicBM25Retriever.from_defaults(**config.model_dump(), index=index)


get_retriever = RetrieverFactory().get_retriever
