"""Chroma retriever."""

from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.schema import BaseNode
from llama_index.vector_stores.chroma import ChromaVectorStore


class ChromaRetriever(VectorIndexRetriever):
    """Chroma retriever."""

    def add_nodes(self, nodes: list[BaseNode], **kwargs) -> None:
        """Support add nodes."""
        self._index.insert_nodes(nodes, **kwargs)

    def persist(self, persist_dir: str, **kwargs) -> None:
        """Support persist.

        Chromadb automatically saves, so there is no need to implement."""

    def query_total_count(self) -> int:
        """Support query total count."""

        vector_store: ChromaVectorStore = self._vector_store

        return vector_store._collection.count()
