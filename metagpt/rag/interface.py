"""RAG Interfaces."""

from typing import Any, Protocol


class RAGObject(Protocol):
    """Support rag add object."""

    def rag_key(self) -> str:
        """For rag search."""

    def model_dump(self) -> dict[str, Any]:
        """For rag persist.

        Pydantic Model don't need to implement this, as there is a built-in function named model_dump.
        """
