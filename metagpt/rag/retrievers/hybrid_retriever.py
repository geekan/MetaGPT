"""Hybrid retriever."""

import copy

from llama_index.core.schema import BaseNode, QueryType

from metagpt.rag.retrievers.base import RAGRetriever


class SimpleHybridRetriever(RAGRetriever):
    """A composite retriever that aggregates search results from multiple retrievers."""

    def __init__(self, *retrievers):
        self.retrievers: list[RAGRetriever] = retrievers
        super().__init__()

    async def _aretrieve(self, query: QueryType, **kwargs):
        """Asynchronously retrieves and aggregates search results from all configured retrievers.

        This method queries each retriever in the `retrievers` list with the given query and
        additional keyword arguments. It then combines the results, ensuring that each node is
        unique, based on the node's ID.
        """
        all_nodes = []
        for retriever in self.retrievers:
            # Prevent retriever changing query
            query_copy = copy.deepcopy(query)
            nodes = await retriever.aretrieve(query_copy, **kwargs)
            all_nodes.extend(nodes)

        # combine all nodes
        result = []
        node_ids = set()
        for n in all_nodes:
            if n.node.node_id not in node_ids:
                result.append(n)
                node_ids.add(n.node.node_id)
        return result

    def add_nodes(self, nodes: list[BaseNode]) -> None:
        """Support add nodes."""
        for r in self.retrievers:
            r.add_nodes(nodes)

    def persist(self, persist_dir: str, **kwargs) -> None:
        """Support persist."""
        for r in self.retrievers:
            r.persist(persist_dir, **kwargs)
