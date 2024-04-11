"""RAG Retriever Factory."""

import copy

import chromadb
import faiss
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.vector_stores.types import BasePydanticVectorStore
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.vector_stores.elasticsearch import ElasticsearchStore
from llama_index.vector_stores.faiss import FaissVectorStore

from metagpt.rag.factories.base import ConfigBasedFactory
from metagpt.rag.retrievers.base import RAGRetriever
from metagpt.rag.retrievers.bm25_retriever import DynamicBM25Retriever
from metagpt.rag.retrievers.chroma_retriever import ChromaRetriever
from metagpt.rag.retrievers.es_retriever import ElasticsearchRetriever
from metagpt.rag.retrievers.faiss_retriever import FAISSRetriever
from metagpt.rag.retrievers.hybrid_retriever import SimpleHybridRetriever
from metagpt.rag.schema import (
    BaseRetrieverConfig,
    BM25RetrieverConfig,
    ChromaRetrieverConfig,
    ElasticsearchKeywordRetrieverConfig,
    ElasticsearchRetrieverConfig,
    FAISSRetrieverConfig,
    IndexRetrieverConfig,
)


class RetrieverFactory(ConfigBasedFactory):
    """Modify creators for dynamically instance implementation."""

    def __init__(self):
        creators = {
            FAISSRetrieverConfig: self._create_faiss_retriever,
            BM25RetrieverConfig: self._create_bm25_retriever,
            ChromaRetrieverConfig: self._create_chroma_retriever,
            ElasticsearchRetrieverConfig: self._create_es_retriever,
            ElasticsearchKeywordRetrieverConfig: self._create_es_retriever,
        }
        super().__init__(creators)

    def get_retriever(self, configs: list[BaseRetrieverConfig] = None, **kwargs) -> RAGRetriever:
        """Creates and returns a retriever instance based on the provided configurations.

        If multiple retrievers, using SimpleHybridRetriever.
        """
        if not configs:
            return self._create_default(**kwargs)

        retrievers = super().get_instances(configs, **kwargs)

        return SimpleHybridRetriever(*retrievers) if len(retrievers) > 1 else retrievers[0]

    def _create_default(self, **kwargs) -> RAGRetriever:
        return self._extract_index(**kwargs).as_retriever()

    def _create_faiss_retriever(self, config: FAISSRetrieverConfig, **kwargs) -> FAISSRetriever:
        vector_store = FaissVectorStore(faiss_index=faiss.IndexFlatL2(config.dimensions))
        config.index = self._build_index_from_vector_store(config, vector_store, **kwargs)

        return FAISSRetriever(**config.model_dump())

    def _create_bm25_retriever(self, config: BM25RetrieverConfig, **kwargs) -> DynamicBM25Retriever:
        config.index = copy.deepcopy(self._extract_index(config, **kwargs))

        return DynamicBM25Retriever(nodes=list(config.index.docstore.docs.values()), **config.model_dump())

    def _create_chroma_retriever(self, config: ChromaRetrieverConfig, **kwargs) -> ChromaRetriever:
        db = chromadb.PersistentClient(path=str(config.persist_path))
        chroma_collection = db.get_or_create_collection(config.collection_name, metadata=config.metadata)

        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        config.index = self._build_index_from_vector_store(config, vector_store, **kwargs)

        return ChromaRetriever(**config.model_dump())

    def _create_es_retriever(self, config: ElasticsearchRetrieverConfig, **kwargs) -> ElasticsearchRetriever:
        vector_store = ElasticsearchStore(**config.store_config.model_dump())
        config.index = self._build_index_from_vector_store(config, vector_store, **kwargs)

        return ElasticsearchRetriever(**config.model_dump())

    def _extract_index(self, config: BaseRetrieverConfig = None, **kwargs) -> VectorStoreIndex:
        return self._val_from_config_or_kwargs("index", config, **kwargs)

    def _build_index_from_vector_store(
        self, config: IndexRetrieverConfig, vector_store: BasePydanticVectorStore, **kwargs
    ) -> VectorStoreIndex:
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        old_index = self._extract_index(config, **kwargs)
        new_index = VectorStoreIndex(
            nodes=list(old_index.docstore.docs.values()),
            storage_context=storage_context,
            embed_model=old_index._embed_model,
        )
        return new_index


get_retriever = RetrieverFactory().get_retriever
