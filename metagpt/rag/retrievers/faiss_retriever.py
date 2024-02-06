from llama_index import Document
from llama_index.retrievers import VectorIndexRetriever


class FAISSRetriever(VectorIndexRetriever):
    def add_docs(self, documents: list[Document]):
        for document in documents:
            self._index.insert(document)
