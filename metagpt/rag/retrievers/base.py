"""Base retriever."""

from abc import abstractmethod

from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import BaseNode, NodeWithScore, QueryType

from metagpt.utils.reflection import check_methods


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
        if cls is ModifiableRAGRetriever:
            return check_methods(C, "add_nodes")
        return NotImplemented

    @abstractmethod
    def add_nodes(self, nodes: list[BaseNode], **kwargs) -> None:
        """To support add docs, must inplement this func"""


class PersistableRAGRetriever(RAGRetriever):
    """Support persistent."""

    @classmethod
    def __subclasshook__(cls, C):
        if cls is PersistableRAGRetriever:
            return check_methods(C, "persist")
        return NotImplemented

    @abstractmethod
    def persist(self, persist_dir: str, **kwargs) -> None:
        """To support persist, must inplement this func"""
