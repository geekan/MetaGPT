"""Retriever schemas"""

from typing import Union

from pydantic import BaseModel


class RetrieverConfig(BaseModel):
    similarity_top_k: int = 5


class FAISSRetrieverConfig(RetrieverConfig):
    dimensions: int = 1536


class BM25RetrieverConfig(RetrieverConfig):
    ...


class RankerConfig(BaseModel):
    top_n: int = 5


class LLMRankerConfig(RankerConfig):
    ...


# If add new config, it is necessary to add the corresponding instance implementation in rag.factory
RetrieverConfigType = Union[FAISSRetrieverConfig, BM25RetrieverConfig]
RankerConfigType = LLMRankerConfig
