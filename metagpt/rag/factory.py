"""Factory for creating retriever, ranker"""
from typing import Any, Callable

import faiss
from llama_index import ServiceContext, StorageContext, VectorStoreIndex
from llama_index.indices.base import BaseIndex
from llama_index.postprocessor import LLMRerank
from llama_index.postprocessor.types import BaseNodePostprocessor
from llama_index.vector_stores.faiss import FaissVectorStore

from metagpt.rag.retrievers.base import RAGRetriever
from metagpt.rag.retrievers.bm25_retriever import DynamicBM25Retriever
from metagpt.rag.retrievers.faiss_retriever import FAISSRetriever
from metagpt.rag.retrievers.hybrid_retriever import SimpleHybridRetriever
from metagpt.rag.schema import (
    BM25RetrieverConfig,
    FAISSRetrieverConfig,
    LLMRankerConfig,
    RankerConfigType,
    RetrieverConfigType,
)


class BaseFactory:
    """
    A base factory class for creating instances based on provided configurations.
    It uses a registry of creator functions mapped to configuration types to instantiate objects dynamically.
    """

    def __init__(self, creators: dict[Any, Callable]):
        """
        Creators is a dictionary mapping configuration types to creator functions.
        The first arg of Creator function should be config.
        """
        self.creators = creators

    def get_instances(self, configs: list[Any] = None, **kwargs) -> list[Any]:
        if not configs:
            return [self._default_instance(**kwargs)]

        return [self._get_instance(config, **kwargs) for config in configs]

    def _get_instance(self, config: Any, **kwargs) -> Any:
        create_func = self.creators.get(type(config))
        if create_func:
            return create_func(config, **kwargs)

        raise ValueError(f"Unknown config: {config}")

    def _default_instance(self, **kwargs) -> Any:
        raise NotImplementedError("This method should be implemented by subclasses.")


class RetrieverFactory(BaseFactory):
    def __init__(self):
        # Dynamically add configuration and corresponding instance implementation.
        creators = {
            FAISSRetrieverConfig: self._create_faiss_retriever,
            BM25RetrieverConfig: self._create_bm25_retriever,
        }
        super().__init__(creators)

    def get_retriever(self, index: BaseIndex, configs: list[RetrieverConfigType] = None) -> RAGRetriever:
        """Creates and returns a retriever instance based on the provided configurations."""
        retrievers = super().get_instances(configs, index=index)

        return (
            SimpleHybridRetriever(*retrievers, service_context=index.service_context)
            if len(retrievers) > 1
            else retrievers[0]
        )

    def _default_instance(self, index: BaseIndex) -> RAGRetriever:
        return index.as_retriever()

    def _create_faiss_retriever(self, config: FAISSRetrieverConfig, index: BaseIndex, **kwargs) -> FAISSRetriever:
        vector_store = FaissVectorStore(faiss_index=faiss.IndexFlatL2(config.dimensions))
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        vector_index = VectorStoreIndex(
            nodes=list(index.docstore.docs.values()),
            storage_context=storage_context,
            service_context=index.service_context,
        )
        return FAISSRetriever(**config.model_dump(), index=vector_index)

    def _create_bm25_retriever(self, config: BM25RetrieverConfig, index: BaseIndex, **kwargs) -> DynamicBM25Retriever:
        return DynamicBM25Retriever.from_defaults(**config.model_dump(), index=index)


class RankerFactory(BaseFactory):
    def __init__(self):
        # Dynamically add configuration and corresponding instance implementation.
        creators = {
            LLMRankerConfig: self._create_llm_ranker,
        }
        super().__init__(creators)

    def get_rankers(
        self, configs: list[RankerConfigType] = None, service_context: ServiceContext = None
    ) -> list[BaseNodePostprocessor]:
        return super().get_instances(configs, service_context=service_context)

    def _default_instance(self, service_context: ServiceContext = None) -> LLMRerank:
        return LLMRerank(top_n=LLMRankerConfig().top_n, service_context=service_context)

    def _create_llm_ranker(self, config: LLMRankerConfig, service_context=None, **kwargs) -> LLMRerank:
        return LLMRerank(**config.model_dump(), service_context=service_context)


get_retriever = RetrieverFactory().get_retriever
get_rankers = RankerFactory().get_rankers
