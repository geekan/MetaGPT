"""RAG pipeline"""
import asyncio

import faiss
from llama_index import (
    ServiceContext,
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.postprocessor import LLMRerank
from llama_index.retrievers import BM25Retriever, VectorIndexRetriever
from llama_index.vector_stores.faiss import FaissVectorStore

from metagpt.const import EXAMPLE_PATH
from metagpt.rag.llm import get_default_llm
from metagpt.rag.retrievers import SimpleHybridRetriever
from metagpt.utils.embedding import get_embedding

DOC_PATH = EXAMPLE_PATH / "data/rag.txt"
QUESTION = "What are key qualities to be a good writer?"
TOPK = 5


def print_result(nodes, extra="retrieve"):
    """print retrieve/rerank result"""
    print("-" * 50)
    print(f"{extra} result")
    for i, node in enumerate(nodes):
        print(f"{i}. {node.text[:10]}..., {node.score}")


async def rag_pipeline():
    """This example run rag pipeline, use faiss&bm25 retriever and llm ranker, will print something like:

    --------------------------------------------------
    faiss retrieve result
    0. I highly r..., 0.3958844542503357
    1. I wrote cu..., 0.41629382967948914
    2. Productivi..., 0.4318419098854065
    3. Some sort ..., 0.45991092920303345
    --------------------------------------------------
    bm25 retrieve result
    0. I highly r..., 0.19445682103516615
    1. Some sort ..., 0.18688966233196197
    2. Productivi..., 0.17071309618829872
    3. I wrote cu..., 0.15878996566615383
    --------------------------------------------------
    hybrid retrieve result
    0. I highly r..., 0.3958844542503357
    1. I wrote cu..., 0.41629382967948914
    2. Productivi..., 0.4318419098854065
    3. Some sort ..., 0.45991092920303345
    --------------------------------------------------
    llm ranker result
    0. Productivi..., 10.0
    1. I wrote cu..., 7.0
    2. I highly r..., 5.0
    """
    # Documents, there are many readers can load documents.
    documents = SimpleDirectoryReader(input_files=[DOC_PATH]).load_data()

    # Service Conext, a bundle of resources for llm/embedding/node_parse.
    service_context = ServiceContext.from_defaults(llm=get_default_llm(), embed_model=get_embedding())

    # Nodes, chunks of documents.
    node_parser = service_context.node_parser
    nodes = node_parser.get_nodes_from_documents(documents)

    # Index-FAISS
    vector_store = FaissVectorStore(faiss_index=faiss.IndexFlatL2(1536))  # dimensions of text-ada-embedding-002
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    vector_index = VectorStoreIndex(nodes=nodes, storage_context=storage_context, service_context=service_context)

    # Retriever-FAISS
    faiss_retriever = VectorIndexRetriever(index=vector_index, similarity_top_k=TOPK)
    faiss_retrieve_nodes = await faiss_retriever.aretrieve(QUESTION)
    print_result(faiss_retrieve_nodes, extra="faiss retrieve")

    # Retriever-BM25
    bm25_retriever = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=TOPK)
    bm25_retrieve_nodes = await bm25_retriever.aretrieve(QUESTION)
    print_result(bm25_retrieve_nodes, extra="bm25 retrieve")

    # Retriever-Hybrid
    hybrid_retriever = SimpleHybridRetriever(faiss_retriever, bm25_retriever)
    hybrid_retrieve_nodes = await hybrid_retriever.aretrieve(QUESTION)
    print_result(hybrid_retrieve_nodes, extra="hybrid retrieve")

    # Ranker-LLM
    llm_ranker = LLMRerank(top_n=TOPK, service_context=service_context)
    llm_rank_nodes = llm_ranker.postprocess_nodes(faiss_retrieve_nodes, query_str=QUESTION)
    print_result(llm_rank_nodes, extra="llm ranker")


async def main():
    """RAG pipeline"""
    await rag_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
