"""Base retriever."""


from abc import abstractmethod

from llama_index import Document
from llama_index.retrievers import BaseRetriever
from llama_index.schema import NodeWithScore, QueryType


class RAGRetriever(BaseRetriever):
    """inherit from llama_index"""

    @abstractmethod
    async def _aretrieve(self, query: QueryType) -> list[NodeWithScore]:
        """retrieve nodes"""

    @abstractmethod
    def add_docs(self, documents: list[Document]) -> None:
        """add docs"""

    def _retrieve(self, query: QueryType) -> list[NodeWithScore]:
        """retrieve nodes"""
