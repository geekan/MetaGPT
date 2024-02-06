from llama_index.retrievers import VectorIndexRetriever
from llama_index.schema import BaseNode


class FAISSRetriever(VectorIndexRetriever):
    def add_nodes(self, nodes: list[BaseNode], **kwargs):
        self._index.insert_nodes(nodes, **kwargs)
