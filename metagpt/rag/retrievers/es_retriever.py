"""Elasticsearch retriever."""

from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.schema import BaseNode


class ElasticsearchRetriever(VectorIndexRetriever):
    """Elasticsearch retriever."""

    def add_nodes(self, nodes: list[BaseNode], **kwargs) -> None:
        """Support add nodes."""
        self._index.insert_nodes(nodes, **kwargs)

    def persist(self, persist_dir: str, **kwargs) -> None:
        """Support persist.

        Elasticsearch automatically saves, so there is no need to implement."""
