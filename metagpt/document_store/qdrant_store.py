from dataclasses import dataclass
from typing import List

from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams
from qdrant_client.models import Filter, PointStruct

from metagpt.document_store.base_store import BaseStore


@dataclass
class QdrantConnection:
    url: str = None
    host: str = None
    port: int = None
    memory: bool = False
    api_key: str = None


class QdrantStore(BaseStore):
    def __init__(self, connect: QdrantConnection):
        if connect.memory:
            self.client = QdrantClient(":memory:")
        elif connect.url:
            self.client = QdrantClient(url=connect.url)
        elif connect.host and connect.port:
            self.client = QdrantClient(host=connect.host, port=connect.port)
        else:
            raise Exception("please check QdrantConnection.")

    def create_collection(self, collection_name: str, vectors_config: VectorParams, force_recreate=False, **kwargs):
        try:
            collection_info = self.client.get_collection(collection_name)
            if force_recreate:
                res = self.client.recreate_collection(collection_name, vectors_config=vectors_config, **kwargs)
                return res
            return collection_info
        except:
            return self.client.recreate_collection(collection_name, vectors_config=vectors_config, **kwargs)

    def delete_collection(self, collection_name, timeout=60):
        self.client.delete_collection(collection_name, timeout=timeout)

    def add(self, collection_name, points: List[PointStruct]):
        # self.client.upload_records()
        self.client.upsert(
            collection_name,
            points,
        )

    def search(self, collection_name: str, query: List[float], query_filter: Filter = None, k=10):
        hits = self.client.search(
            collection_name=collection_name, query_vector=query, query_filter=query_filter, limit=k
        )
        return [hit.__dict__ for hit in hits]

    def write(self, *args, **kwargs):
        pass
