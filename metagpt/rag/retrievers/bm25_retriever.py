from llama_index import Document
from llama_index.retrievers import BM25Retriever


class DynamicBM25Retriever(BM25Retriever):
    def add_docs(self, documents: list[Document]):
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            raise ImportError("Please install rank_bm25: pip install rank-bm25")

        self._nodes.extend(documents)
        self._corpus = [self._tokenizer(node.get_content()) for node in self._nodes]
        self.bm25 = BM25Okapi(self._corpus)
