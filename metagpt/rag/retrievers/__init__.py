__all__ = ["SimpleHybridRetriever", "get_retriever"]

from llama_index import (
    ServiceContext,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.retrievers import BaseRetriever, BM25Retriever, VectorIndexRetriever
from llama_index.schema import BaseNode
from llama_index.vector_stores.faiss import FaissVectorStore

from metagpt.rag.retrievers.hybrid import SimpleHybridRetriever
from metagpt.rag.schema import RetrieverConfig, FAISSRetrieverConfig, BM25RetrieverConfig
import faiss


def get_retriever(
    nodes: list[BaseNode], configs: list[RetrieverConfig] = None, service_context: ServiceContext = None
) -> BaseRetriever:
    if not configs:
        return _default_retriever(nodes, service_context)

    retrivers = [_get_retriever(nodes, config, service_context) for config in configs]

    return SimpleHybridRetriever(*retrivers, service_context=service_context) if len(retrivers) > 1 else retrivers[0]


def _default_retriever(nodes: list[BaseNode], service_context: ServiceContext = None) -> BaseRetriever:
    return VectorStoreIndex(nodes=nodes, service_context=service_context).as_retriever()


def _get_retriever(
    nodes: list[BaseNode], config: RetrieverConfig, service_context: ServiceContext = None
) -> BaseRetriever:
    retriever_factory = {
        FAISSRetrieverConfig: _create_faiss_retriever,
        BM25RetrieverConfig: _create_bm25_retriever,
    }

    create_func = retriever_factory.get(type(config))
    if create_func:
        return create_func(nodes, config, service_context)

    raise ValueError(f"Unknown retriever config: {config}")


def _create_faiss_retriever(nodes: list[BaseNode], config: RetrieverConfig, service_context: ServiceContext):
    vector_store = FaissVectorStore(faiss_index=faiss.IndexFlatL2(config.dimensions))
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    vector_index = VectorStoreIndex(nodes=nodes, storage_context=storage_context, service_context=service_context)
    return VectorIndexRetriever(index=vector_index, similarity_top_k=config.similarity_top_k)


def _create_bm25_retriever(nodes: list[BaseNode], config: RetrieverConfig, service_context: ServiceContext = None):
    return BM25Retriever.from_defaults(**config.model_dump(), nodes=nodes)
