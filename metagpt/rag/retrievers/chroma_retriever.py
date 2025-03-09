"""Chroma retriever."""

from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.schema import BaseNode
from llama_index.vector_stores.chroma import ChromaVectorStore


class ChromaRetriever(VectorIndexRetriever):
    """Chroma retriever."""

    @property
    def vector_store(self) -> ChromaVectorStore:
        return self._vector_store

    def add_nodes(self, nodes: list[BaseNode], **kwargs) -> None:
        """Support add nodes."""
        self._index.insert_nodes(nodes, **kwargs)

    def persist(self, persist_dir: str, **kwargs) -> None:
        """Support persist.

        Chromadb automatically saves, so there is no need to implement."""

    def query_total_count(self) -> int:
        """Support query total count."""

        return self.vector_store._collection.count()

    def clear(self, **kwargs) -> None:
        """Support deleting all nodes."""

        ids = self.vector_store._collection.get()["ids"]
        if ids:
            self.vector_store._collection.delete(ids=ids)
