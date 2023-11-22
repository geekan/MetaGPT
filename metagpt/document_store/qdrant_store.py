from dataclasses import dataclass
from typing import List

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, PointStruct, VectorParams

from metagpt.document_store.base_store import BaseStore


@dataclass
class QdrantConnection:
    """
    Args:
        url: qdrant url
        host: qdrant host
        port: qdrant port
        memory: qdrant service use memory mode
        api_key: qdrant cloud api_key
    """

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
            self.client = QdrantClient(url=connect.url, api_key=connect.api_key)
        elif connect.host and connect.port:
            self.client = QdrantClient(host=connect.host, port=connect.port, api_key=connect.api_key)
        else:
            raise Exception("please check QdrantConnection.")

    def create_collection(
        self,
        collection_name: str,
        vectors_config: VectorParams,
        force_recreate=False,
        **kwargs,
    ):
        """
        create a collection
        Args:
            collection_name: collection name
            vectors_config: VectorParams object,detail in https://github.com/qdrant/qdrant-client
            force_recreate: default is False, if True, will delete exists collection,then create it
            **kwargs:

        Returns:

        """
        try:
            self.client.get_collection(collection_name)
            if force_recreate:
                res = self.client.recreate_collection(collection_name, vectors_config=vectors_config, **kwargs)
                return res
            return True
        except:  # noqa: E722
            return self.client.recreate_collection(collection_name, vectors_config=vectors_config, **kwargs)

    def has_collection(self, collection_name: str):
        try:
            self.client.get_collection(collection_name)
            return True
        except:  # noqa: E722
            return False

    def delete_collection(self, collection_name: str, timeout=60):
        res = self.client.delete_collection(collection_name, timeout=timeout)
        if not res:
            raise Exception(f"Delete collection {collection_name} failed.")

    def add(self, collection_name: str, points: List[PointStruct]):
        """
        add some vector data to qdrant
        Args:
            collection_name: collection name
            points: list of PointStruct object, about PointStruct detail in https://github.com/qdrant/qdrant-client

        Returns: NoneX

        """
        # self.client.upload_records()
        self.client.upsert(
            collection_name,
            points,
        )

    def search(
        self,
        collection_name: str,
        query: List[float],
        query_filter: Filter = None,
        k=10,
        return_vector=False,
    ):
        """
        vector search
        Args:
            collection_name: qdrant collection name
            query: input vector
            query_filter: Filter object, detail in https://github.com/qdrant/qdrant-client
            k: return the most similar k pieces of data
            return_vector: whether return vector

        Returns: list of dict

        """
        hits = self.client.search(
            collection_name=collection_name,
            query_vector=query,
            query_filter=query_filter,
            limit=k,
            with_vectors=return_vector,
        )
        return [hit.__dict__ for hit in hits]

    def write(self, *args, **kwargs):
        pass
