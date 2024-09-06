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
        if not query:
            return []

        nodes: list[NodeWithScore] = self.rag_engine.retrieve(query)

        memories = []
        for node in nodes:
            item: LongTermMemoryItem = node.metadata["obj"]
            memories.append(item.user_message)
            memories.append(item.ai_message)

        return memories

    def add(self, item: LongTermMemoryItem):
        if not item:
            return

        self.rag_engine.add_objs([item])
