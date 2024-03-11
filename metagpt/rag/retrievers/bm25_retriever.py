"""BM25 retriever."""

from llama_index.core.schema import BaseNode
from llama_index.retrievers.bm25 import BM25Retriever
from rank_bm25 import BM25Okapi


class DynamicBM25Retriever(BM25Retriever):
    """BM25 retriever."""

    def add_nodes(self, nodes: list[BaseNode], **kwargs) -> None:
        """Support add nodes"""
        self._nodes.extend(nodes)
        self._corpus = [self._tokenizer(node.get_content()) for node in self._nodes]
        self.bm25 = BM25Okapi(self._corpus)
