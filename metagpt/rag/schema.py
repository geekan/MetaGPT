"""Retriever schemas"""

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
