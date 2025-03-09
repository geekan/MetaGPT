"""
This module implements a memory system combining short-term and long-term storage for AI role memory management.
It utilizes a RAG (Retrieval-Augmented Generation) engine for long-term memory storage and retrieval.
"""

from typing import TYPE_CHECKING, Any, Optional

from pydantic import Field

from metagpt.actions import UserRequirement
from metagpt.const import TEAMLEADER_NAME
from metagpt.logs import logger
from metagpt.memory import Memory
from metagpt.schema import LongTermMemoryItem, Message
from metagpt.utils.common import any_to_str
from metagpt.utils.exceptions import handle_exception

if TYPE_CHECKING:
    from llama_index.core.schema import NodeWithScore

    from metagpt.rag.engines import SimpleEngine


class RoleZeroLongTermMemory(Memory):
    """
    Implements a memory system combining short-term and long-term storage using a RAG engine.
    Transfers old memories to long-term storage when short-term capacity is reached.
    Retrieves combined short-term and long-term memories as needed.
    """

    persist_path: str = Field(default=".role_memory_data", description="The directory to save data.")
    collection_name: str = Field(default="role_zero", description="The name of the collection, such as the role name.")
    memory_k: int = Field(default=200, description="The capacity of short-term memory.")
    similarity_top_k: int = Field(default=5, description="The number of long-term memories to retrieve.")
    use_llm_ranker: bool = Field(default=False, description="Whether to use LLM Reranker to get better result.")

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
            ChromaRetrieverConfig(
                persist_path=self.persist_path,
                collection_name=self.collection_name,
                similarity_top_k=self.similarity_top_k,
            )
        ]
        ranker_configs = [LLMRankerConfig()] if self.use_llm_ranker else []

        rag_engine = SimpleEngine.from_objs(retriever_configs=retriever_configs, ranker_configs=ranker_configs)

        return rag_engine

    def add(self, message: Message):
        """Add a new message and potentially transfer it to long-term memory."""

        super().add(message)

        if not self._should_use_longterm_memory_for_add():
            return

        self._transfer_to_longterm_memory()

    def get(self, k=0) -> list[Message]:
        """Return recent memories and optionally combines them with related long-term memories."""

        memories = super().get(k)

        if not self._should_use_longterm_memory_for_get(k=k):
            return memories

        query = self._build_longterm_memory_query()
        related_memories = self._fetch_longterm_memories(query)
        logger.info(f"Fetched {len(related_memories)} long-term memories.")

        final_memories = related_memories + memories

        return final_memories

    def _should_use_longterm_memory_for_add(self) -> bool:
        """Determines if long-term memory should be used for add."""

        return self.count() > self.memory_k

    def _should_use_longterm_memory_for_get(self, k: int) -> bool:
        """Determines if long-term memory should be used for get.

        Long-term memory is used if:
        - k is not 0.
        - The last message is from user requirement.
        - The count of recent memories is greater than self.memory_k.
        """

        conds = [
            k != 0,
            self._is_last_message_from_user_requirement(),
            self.count() > self.memory_k,
        ]

        return all(conds)

    def _transfer_to_longterm_memory(self):
        item = self._get_longterm_memory_item()
        self._add_to_longterm_memory(item)

    def _get_longterm_memory_item(self) -> Optional[LongTermMemoryItem]:
        """Retrieves the most recent message before the last k messages."""

        index = -(self.memory_k + 1)
        message = self.get_by_position(index)

        return LongTermMemoryItem(message=message) if message else None

    @handle_exception
    def _add_to_longterm_memory(self, item: LongTermMemoryItem):
        """Adds a long-term memory item to the RAG engine.

        If adding long-term memory fails, it will only log the error without interrupting program execution.
        """

        if not item or not item.message.content:
            return

        self.rag_engine.add_objs([item])

    @handle_exception(default_return=[])
    def _fetch_longterm_memories(self, query: str) -> list[Message]:
        """Fetches long-term memories based on a query.

        If fetching long-term memories fails, it will return the default value (an empty list) without interrupting program execution.

        Args:
            query (str): The query string to search for relevant memories.

        Returns:
            list[Message]: A list of user and AI messages related to the query.
        """

        if not query:
            return []

        nodes = self.rag_engine.retrieve(query)
        items = self._get_items_from_nodes(nodes)
        memories = [item.message for item in items]

        return memories

    def _get_items_from_nodes(self, nodes: list["NodeWithScore"]) -> list[LongTermMemoryItem]:
        """Get items from nodes and arrange them in order of their `created_at`."""

        items: list[LongTermMemoryItem] = [node.metadata["obj"] for node in nodes]
        items.sort(key=lambda item: item.created_at)

        return items

    def _build_longterm_memory_query(self) -> str:
        """Build the content used to query related long-term memory.

        Default is to get the most recent user message, or an empty string if none is found.
        """

        message = self._get_the_last_message()

        return message.content if message else ""

    def _get_the_last_message(self) -> Optional[Message]:
        if not self.count():
            return None

        return self.get_by_position(-1)

    def _is_last_message_from_user_requirement(self) -> bool:
        """Checks if the last message is from a user requirement or sent by the team leader."""

        message = self._get_the_last_message()

        if not message:
            return False

        is_user_message = message.is_user_message()
        cause_by_user_requirement = message.cause_by == any_to_str(UserRequirement)
        sent_from_team_leader = message.sent_from == TEAMLEADER_NAME

        return is_user_message and (cause_by_user_requirement or sent_from_team_leader)
