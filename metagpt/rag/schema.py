"""RAG schemas"""

from typing import Union

from pydantic import BaseModel, Field


class RetrieverConfig(BaseModel):
    """Common config for retrievers."""

    similarity_top_k: int = Field(default=5, description="Number of top-k similar results to return during retrieval.")


class FAISSRetrieverConfig(RetrieverConfig):
    """Config for FAISS-based retrievers."""

    dimensions: int = Field(default=1536, description="Dimensionality of the vectors for FAISS index construction.")


class BM25RetrieverConfig(RetrieverConfig):
    """Config for BM25-based retrievers."""


class RankerConfig(BaseModel):
    """Common config for rankers."""

    top_n: int = 5


class LLMRankerConfig(RankerConfig):
    """Config for LLM-based rankers."""


# If add new config, it is necessary to add the corresponding instance implementation in rag.factory
RetrieverConfigType = Union[FAISSRetrieverConfig, BM25RetrieverConfig]
RankerConfigType = LLMRankerConfig
