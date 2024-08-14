from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pymilvus import MilvusClient, DataType

from metagpt.document_store.base_store import BaseStore

@dataclass
class MilvusConnection:
    """
    Args:
        uri: milvus url
        token: milvus token
    """

    uri: str = None
    token: str = None


class MilvusStore(BaseStore):
    def __init__(self, connect: MilvusConnection):
        if not connect.uri:
            raise Exception("please check MilvusConnection, uri must be set.")
        self.client = MilvusClient(
            uri=connect.uri,
            token=connect.token
        )

    def create_collection(
        self,
        collection_name: str,
        dim: int,
        enable_dynamic_schema: bool = True
    ):
        if self.client.has_collection(collection_name=collection_name):
            self.client.drop_collection(collection_name=collection_name)

        schema = self.client.create_schema(
            auto_id=False,
            enable_dynamic_field=False,
        )
        schema.add_field(field_name="id", datatype=DataType.VARCHAR, is_primary=True, max_length=36)
        schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=dim)

        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            index_type="AUTOINDEX",
            metric_type="COSINE"
        )

        self.client.create_collection(
            collection_name=collection_name,
            schema=schema,
            index_params=index_params,
            enable_dynamic_schema=enable_dynamic_schema
        )

    @staticmethod
    def build_filter(key, value) -> str:
        if isinstance(value, str):
            filter_expression = f'{key} == "{value}"'
        else:
            if isinstance(value, list):
                filter_expression = f'{key} in {value}'
            else:
                filter_expression = f'{key} == {value}'

        return filter_expression

    def search(
        self,
        collection_name: str,
        query: List[float],
        filter: Dict[str, str | int | list[int]] = None,
        limit: int = 10,
        output_fields: Optional[List[str]] = None,
    ) -> List[dict]:
        filter_expression = ''

        for key, value in filter.items():
            filter_expression += f'{self.build_filter(key, value)} and '
        print(filter_expression)

        res = self.client.search(
            collection_name=collection_name,
            data=[query],
            filter=filter_expression,
            limit=limit,
            output_fields=output_fields,
        )[0]

        return res

    def add(
        self,
        collection_name: str,
        _ids: List[str],
        vector: List[List[float]],
        metadata: List[Dict[str, Any]]
    ):
        data = dict()

        for i, id in enumerate(_ids):
            data['id'] = id
            data['vector'] = vector[i]
            data['metadata'] = metadata[i]

        self.client.upsert(
            collection_name=collection_name,
            data=data
        )

    def delete(
        self,
        collection_name: str,
        _ids: List[str]
    ):
        self.client.delete(
            collection_name=collection_name,
            ids=_ids
        )

    def write(self, *args, **kwargs):
        pass
