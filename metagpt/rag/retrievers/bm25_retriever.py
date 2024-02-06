from llama_index.retrievers import BM25Retriever
from llama_index.schema import BaseNode


class DynamicBM25Retriever(BM25Retriever):
    def add_nodes(self, nodes: list[BaseNode], **kwargs):
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            raise ImportError("Please install rank_bm25: pip install rank-bm25")

        self._nodes.extend(nodes)
        self._corpus = [self._tokenizer(node.get_content()) for node in self._nodes]
        self.bm25 = BM25Okapi(self._corpus)
