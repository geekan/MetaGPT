from typing import TypedDict

from metagpt.document_store.base_store import BaseStore

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams


class MilvusConnection(TypedDict):
    host: str
    port: str
    url: str


class QdrantStore(BaseStore):
    def __init__(self, connect):
        pass
