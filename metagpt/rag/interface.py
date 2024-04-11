"""RAG Interfaces."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class RAGObject(Protocol):
    """Support rag add object."""

    def rag_key(self) -> str:
        """For rag search."""

    def model_dump_json(self) -> str:
        """For rag persist.

        Pydantic Model don't need to implement this, as there is a built-in function named model_dump_json.
        """


@runtime_checkable
class NoEmbedding(Protocol):
    """Some retriever does not require embeddings, e.g. BM25"""

    _no_embedding: bool
