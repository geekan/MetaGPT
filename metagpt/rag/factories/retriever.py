"""RAG Retriever Factory."""

from functools import wraps

import chromadb
import faiss
from llama_index.core import PropertyGraphIndex, StorageContext, VectorStoreIndex
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.indices.property_graph import PGRetriever
from llama_index.core.schema import BaseNode
from llama_index.core.vector_stores.types import BasePydanticVectorStore
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.vector_stores.elasticsearch import ElasticsearchStore
from llama_index.vector_stores.faiss import FaissVectorStore
from llama_index.vector_stores.milvus import MilvusVectorStore

from metagpt.rag.factories.base import ConfigBasedFactory
from metagpt.rag.retrievers.base import RAGRetriever
from metagpt.rag.retrievers.bm25_retriever import DynamicBM25Retriever
from metagpt.rag.retrievers.chroma_retriever import ChromaRetriever
from metagpt.rag.retrievers.es_retriever import ElasticsearchRetriever
from metagpt.rag.retrievers.faiss_retriever import FAISSRetriever
from metagpt.rag.retrievers.hybrid_retriever import SimpleHybridRetriever
from metagpt.rag.retrievers.milvus_retriever import MilvusRetriever
from metagpt.rag.schema import (
    BaseRetrieverConfig,
    BM25RetrieverConfig,
    ChromaRetrieverConfig,
    ElasticsearchKeywordRetrieverConfig,
    ElasticsearchRetrieverConfig,
    FAISSRetrieverConfig,
    MilvusRetrieverConfig,
    Neo4jPGRetrieverConfig,
)


def get_or_build_index(build_index_func):
    """Decorator to get or build an index.

    Get index using `_extract_index` method, if not found, using build_index_func.
    """

    @wraps(build_index_func)
    def wrapper(self, config, **kwargs):
        index = self._extract_index(config, **kwargs)
        if index is not None:
            return index
        return build_index_func(self, config, **kwargs)

    return wrapper


class RetrieverFactory(ConfigBasedFactory):
    """Modify creators for dynamically instance implementation."""

    def __init__(self):
        creators = {
            FAISSRetrieverConfig: self._create_faiss_retriever,
            BM25RetrieverConfig: self._create_bm25_retriever,
            ChromaRetrieverConfig: self._create_chroma_retriever,
            ElasticsearchRetrieverConfig: self._create_es_retriever,
            ElasticsearchKeywordRetrieverConfig: self._create_es_retriever,
            MilvusRetrieverConfig: self._create_milvus_retriever,
            Neo4jPGRetrieverConfig: self._create_neo4j_pg_retriever,
        }
        super().__init__(creators)

    def get_retriever(
        self, configs: list[BaseRetrieverConfig] = None, build_graph: bool = False, **kwargs
    ) -> RAGRetriever:
        """Creates and returns a retriever instance based on the provided configurations.

        If multiple retrievers, using SimpleHybridRetriever.
        If build_graph is True and no graph-related retriver_config is provided,
        the default is to use memory for graph attribute storage and retrieval.
        If a graph-related retriever_config is provided,
        the build_graph parameter is ignored and the configured one is used directly.
        """
        if not configs:
            return self._create_default(build_graph=build_graph, **kwargs)

        retrievers = super().get_instances(configs, **kwargs)
        has_pg_retriever = any(isinstance(retriever, PGRetriever) for retriever in retrievers)

        if build_graph and not has_pg_retriever:
            pg_index = self._extract_index(None, **kwargs) or self._build_default_pg_index(**kwargs)
            retrievers.append(pg_index.as_retriever())

        return SimpleHybridRetriever(*retrievers) if len(retrievers) > 1 else retrievers[0]

    def _create_default(self, build_graph: bool = False, **kwargs) -> RAGRetriever:
        vector_index = self._extract_index(None, **kwargs) or self._build_default_vector_index(**kwargs)
        retrievers = [vector_index.as_retriever()]

        if build_graph:
            pg_index = self._extract_index(None, **kwargs) or self._build_default_pg_index(**kwargs)
            retrievers.append(pg_index.as_retriever())

        return SimpleHybridRetriever(*retrievers) if len(retrievers) > 1 else retrievers[0]

    def _create_milvus_retriever(self, config: MilvusRetrieverConfig, **kwargs) -> MilvusRetriever:
        config.index = self._build_milvus_index(config, **kwargs)

        return MilvusRetriever(**config.model_dump())

    def _create_faiss_retriever(self, config: FAISSRetrieverConfig, **kwargs) -> FAISSRetriever:
        config.index = self._build_faiss_index(config, **kwargs)

        return FAISSRetriever(**config.model_dump())

    def _create_bm25_retriever(self, config: BM25RetrieverConfig, **kwargs) -> DynamicBM25Retriever:
        index = self._extract_index(config, **kwargs)
        nodes = list(index.docstore.docs.values()) if index else self._extract_nodes(config, **kwargs)

        return DynamicBM25Retriever(nodes=nodes, **config.model_dump())

    def _create_chroma_retriever(self, config: ChromaRetrieverConfig, **kwargs) -> ChromaRetriever:
        config.index = self._build_chroma_index(config, **kwargs)

        return ChromaRetriever(**config.model_dump())

    def _create_es_retriever(self, config: ElasticsearchRetrieverConfig, **kwargs) -> ElasticsearchRetriever:
        config.index = self._build_es_index(config, **kwargs)

        return ElasticsearchRetriever(**config.model_dump())

    def _create_neo4j_pg_retriever(self, config: Neo4jPGRetrieverConfig, **kwargs) -> PGRetriever:
        graph_index = self._build_neo4j_pg_index(config, **kwargs)
        return graph_index.as_retriever(**config.model_dump())

    def _extract_index(self, config: BaseRetrieverConfig = None, **kwargs) -> VectorStoreIndex:
        return self._val_from_config_or_kwargs("index", config, **kwargs)

    def _extract_nodes(self, config: BaseRetrieverConfig = None, **kwargs) -> list[BaseNode]:
        return self._val_from_config_or_kwargs("nodes", config, **kwargs)

    def _extract_embed_model(self, config: BaseRetrieverConfig = None, **kwargs) -> BaseEmbedding:
        return self._val_from_config_or_kwargs("embed_model", config, **kwargs)

    def _build_default_vector_index(self, **kwargs) -> VectorStoreIndex:
        vector_index = VectorStoreIndex(
            nodes=self._extract_nodes(**kwargs),
            embed_model=self._extract_embed_model(**kwargs),
        )
        return vector_index

    def _build_default_pg_index(self, **kwargs):
        # build default PropertyGraphIndex
        pg_index = PropertyGraphIndex(
            nodes=self._extract_nodes(**kwargs),
            embed_model=self._extract_embed_model(**kwargs),
        )
        return pg_index

    @get_or_build_index
    def _build_faiss_index(self, config: FAISSRetrieverConfig, **kwargs) -> VectorStoreIndex:
        vector_store = FaissVectorStore(faiss_index=faiss.IndexFlatL2(config.dimensions))

        return self._build_index_from_vector_store(config, vector_store, **kwargs)

    @get_or_build_index
    def _build_chroma_index(self, config: ChromaRetrieverConfig, **kwargs) -> VectorStoreIndex:
        db = chromadb.PersistentClient(path=str(config.persist_path))
        chroma_collection = db.get_or_create_collection(config.collection_name, metadata=config.metadata)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

        return self._build_index_from_vector_store(config, vector_store, **kwargs)

    @get_or_build_index
    def _build_milvus_index(self, config: MilvusRetrieverConfig, **kwargs) -> VectorStoreIndex:
        vector_store = MilvusVectorStore(
            uri=config.uri, collection_name=config.collection_name, token=config.token, dim=config.dimensions
        )

        return self._build_index_from_vector_store(config, vector_store, **kwargs)

    @get_or_build_index
    def _build_es_index(self, config: ElasticsearchRetrieverConfig, **kwargs) -> VectorStoreIndex:
        vector_store = ElasticsearchStore(**config.store_config.model_dump())

        return self._build_index_from_vector_store(config, vector_store, **kwargs)

    @get_or_build_index
    def _build_neo4j_pg_index(self, config: Neo4jPGRetrieverConfig, **kwargs) -> PropertyGraphIndex:
        graph_store = Neo4jPropertyGraphStore(**config.store_config.model_dump())
        graph_index = PropertyGraphIndex(
            nodes=self._extract_nodes(**kwargs),
            property_graph_store=graph_store,
            embed_model=self._extract_embed_model(**kwargs),
            **config.model_dump(),
        )
        return graph_index

    def _build_index_from_vector_store(
        self, config: BaseRetrieverConfig, vector_store: BasePydanticVectorStore, **kwargs
    ) -> VectorStoreIndex:
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex(
            nodes=self._extract_nodes(config, **kwargs),
            storage_context=storage_context,
            embed_model=self._extract_embed_model(config, **kwargs),
        )

        return index


get_retriever = RetrieverFactory().get_retriever
