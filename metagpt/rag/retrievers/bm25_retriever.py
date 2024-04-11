"""BM25 retriever."""
from typing import Callable, Optional

from llama_index.core import VectorStoreIndex
from llama_index.core.callbacks.base import CallbackManager
from llama_index.core.constants import DEFAULT_SIMILARITY_TOP_K
from llama_index.core.schema import BaseNode, IndexNode
from llama_index.retrievers.bm25 import BM25Retriever
from rank_bm25 import BM25Okapi


class DynamicBM25Retriever(BM25Retriever):
    """BM25 retriever."""

    def __init__(
        self,
        nodes: list[BaseNode],
        tokenizer: Optional[Callable[[str], list[str]]] = None,
        similarity_top_k: int = DEFAULT_SIMILARITY_TOP_K,
        callback_manager: Optional[CallbackManager] = None,
        objects: Optional[list[IndexNode]] = None,
        object_map: Optional[dict] = None,
        verbose: bool = False,
        index: VectorStoreIndex = None,
    ) -> None:
        super().__init__(
            nodes=nodes,
            tokenizer=tokenizer,
            similarity_top_k=similarity_top_k,
            callback_manager=callback_manager,
            object_map=object_map,
            objects=objects,
            verbose=verbose,
        )
        self._index = index

    def add_nodes(self, nodes: list[BaseNode], **kwargs) -> None:
        """Support add nodes."""
        self._nodes.extend(nodes)
        self._corpus = [self._tokenizer(node.get_content()) for node in self._nodes]
        self.bm25 = BM25Okapi(self._corpus)

        self._index.insert_nodes(nodes, **kwargs)

    def persist(self, persist_dir: str, **kwargs) -> None:
        """Support persist."""
        self._index.storage_context.persist(persist_dir)
