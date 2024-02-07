from typing import Protocol


class RAGObject(Protocol):
    def rag_key(self) -> str:
        """for rag search"""
