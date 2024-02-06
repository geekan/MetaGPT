"""Hybrid retriever."""
from llama_index import Document, ServiceContext
from llama_index.schema import QueryType

from metagpt.rag.retrievers.base import RAGRetriever


class SimpleHybridRetriever(RAGRetriever):
    """
    SimpleHybridRetriever is a composite retriever that aggregates search results from multiple retrievers.
    """

    def __init__(self, *retrievers, service_context: ServiceContext = None):
        self.retrievers: list[RAGRetriever] = retrievers
        self.service_context = service_context
        super().__init__()

    async def _aretrieve(self, query: QueryType, **kwargs):
        """
        Asynchronously retrieves and aggregates search results from all configured retrievers.

        This method queries each retriever in the `retrievers` list with the given query and
        additional keyword arguments. It then combines the results, ensuring that each node is
        unique, based on the node's ID.
        """
        all_nodes = []
        for retriever in self.retrievers:
            nodes = await retriever.aretrieve(query, **kwargs)
            all_nodes.extend(nodes)

        # combine all nodes
        result = []
        node_ids = set()
        for n in all_nodes:
            if n.node.node_id not in node_ids:
                result.append(n)
                node_ids.add(n.node.node_id)
        return result

    def add_docs(self, documents: list[Document]):
        for r in self.retrievers:
            r.add_docs(documents)
