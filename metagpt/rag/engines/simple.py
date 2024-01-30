"""Simple Engine."""
from typing import Optional

from llama_index import ServiceContext, SimpleDirectoryReader, VectorStoreIndex
from llama_index.constants import DEFAULT_SIMILARITY_TOP_K
from llama_index.embeddings.base import BaseEmbedding
from llama_index.llms.llm import LLM
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.retrievers import VectorIndexRetriever

from metagpt.rag.llm import get_default_llm
from metagpt.utils.embedding import get_embedding


class SimpleEngine(RetrieverQueryEngine):
    """
    SimpleEngine is a search engine that uses a vector index for retrieving documents.
    """

    @classmethod
    def from_docs(
        cls,
        input_dir: str = None,
        input_files: list = None,
        embed_model: BaseEmbedding = None,
        llm: LLM = None,
        # node parser kwargs
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        # retrieve kwargs
        similarity_top_k: int = DEFAULT_SIMILARITY_TOP_K,
    ) -> "SimpleEngine":
        """This engine is designed to be simple and straightforward"""
        documents = SimpleDirectoryReader(input_dir=input_dir, input_files=input_files).load_data()
        service_context = ServiceContext.from_defaults(
            embed_model=embed_model or get_embedding(),
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            llm=llm or get_default_llm(),
        )
        index = VectorStoreIndex.from_documents(documents, service_context=service_context)
        retriever = VectorIndexRetriever(index=index, similarity_top_k=similarity_top_k)

        return SimpleEngine(retriever=retriever)

    async def asearch(self, content: str, **kwargs) -> str:
        """Inplement tools.SearchInterface"""
        return await self.aquery(content)
