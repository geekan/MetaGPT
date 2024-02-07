"""Base retriever."""


from abc import abstractmethod

from llama_index.retrievers import BaseRetriever
from llama_index.schema import BaseNode, NodeWithScore, QueryType


class RAGRetriever(BaseRetriever):
    """Inherit from llama_index"""

    @abstractmethod
    async def _aretrieve(self, query: QueryType) -> list[NodeWithScore]:
        """Retrieve nodes"""

    def _retrieve(self, query: QueryType) -> list[NodeWithScore]:
        """Retrieve nodes"""


class ModifiableRAGRetriever(RAGRetriever):
    """Support modification."""

    @classmethod
    def __subclasshook__(cls, C):
        if any("add_nodes" in B.__dict__ for B in C.__mro__):
            return True
        return NotImplemented

    @abstractmethod
    def add_nodes(self, nodes: list[BaseNode], **kwargs) -> None:
        """To support add docs, must inplement this func"""
