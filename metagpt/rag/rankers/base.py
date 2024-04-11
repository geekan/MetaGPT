"""Base Ranker."""

from abc import abstractmethod
from typing import Optional

from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle


class RAGRanker(BaseNodePostprocessor):
    """inherit from llama_index"""

    @abstractmethod
    def _postprocess_nodes(
        self,
        nodes: list[NodeWithScore],
        query_bundle: Optional[QueryBundle] = None,
    ) -> list[NodeWithScore]:
        """postprocess nodes."""
