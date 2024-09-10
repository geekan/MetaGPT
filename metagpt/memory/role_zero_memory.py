from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from metagpt.schema import LongTermMemoryItem, Message

if TYPE_CHECKING:
    from llama_index.core.schema import NodeWithScore

    from metagpt.rag.engines import SimpleEngine


class RoleZeroLongTermMemory(BaseModel):
    persist_path: str = Field(default=".role_memory_data", description="The directory to save data.")
    collection_name: str = Field(default="role_zero", description="The name of the collection, such as the role name.")

    _rag_engine: Any = None

    @property
    def rag_engine(self) -> "SimpleEngine":
        if self._rag_engine is None:
            self._rag_engine = self._resolve_rag_engine()

        return self._rag_engine

    def _resolve_rag_engine(self) -> "SimpleEngine":
        """Lazy loading of the RAG engine components, ensuring they are only loaded when needed.

        It uses `Chroma` for retrieval and `LLMRanker` for ranking.
        """

        try:
            from metagpt.rag.engines import SimpleEngine
            from metagpt.rag.schema import ChromaRetrieverConfig, LLMRankerConfig
        except ImportError:
            raise ImportError("To use the RoleZeroMemory, you need to install the rag module.")

        retriever_configs = [
            ChromaRetrieverConfig(persist_path=self.persist_path, collection_name=self.collection_name)
        ]
        ranker_configs = [LLMRankerConfig()]

        rag_engine = SimpleEngine.from_objs(retriever_configs=retriever_configs, ranker_configs=ranker_configs)

        return rag_engine

    def fetch(self, query: str) -> list[Message]:
        """Fetches long-term memories based on a query.

        Args:
            query (str): The query string to search for relevant memories.

        Returns:
            list[Message]: A list of user and AI messages related to the query.
        """

        if not query:
            return []

        nodes = self.rag_engine.retrieve(query)
        items = self._get_items_from_nodes(nodes)

        memories = []
        for item in items:
            memories.append(item.user_message)
            memories.append(item.ai_message)

        return memories

    def add(self, item: LongTermMemoryItem):
        """Adds a long-term memory item to the RAG engine.

        Args:
            item (LongTermMemoryItem): The memory item containing user and AI messages.
        """

        if not item:
            return

        self.rag_engine.add_objs([item])

    def _get_items_from_nodes(self, nodes: list["NodeWithScore"]) -> list[LongTermMemoryItem]:
        """Get items from nodes and arrange them in order of their `created_at`."""

        items: list[LongTermMemoryItem] = [node.metadata["obj"] for node in nodes]
        items.sort(key=lambda item: item.created_at)

        return items
