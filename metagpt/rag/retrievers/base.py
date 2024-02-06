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

    def add_nodes(self, nodes: list[BaseNode], **kwargs) -> None:
        """To support add docs, must inplement this func"""
