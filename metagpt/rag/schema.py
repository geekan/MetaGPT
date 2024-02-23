"""RAG schemas."""

from typing import Any

from llama_index.core.indices.base import BaseIndex
from pydantic import BaseModel, ConfigDict, Field


class BaseRetrieverConfig(BaseModel):
    """Common config for retrievers.

    If add new subconfig, it is necessary to add the corresponding instance implementation in rag.factory.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    similarity_top_k: int = Field(default=5, description="Number of top-k similar results to return during retrieval.")


class IndexRetrieverConfig(BaseRetrieverConfig):
    """Config for Index-basd retrievers."""

    index: BaseIndex = Field(default=None, description="Index for retriver")


class FAISSRetrieverConfig(IndexRetrieverConfig):
    """Config for FAISS-based retrievers."""

    dimensions: int = Field(default=1536, description="Dimensionality of the vectors for FAISS index construction.")


class BM25RetrieverConfig(IndexRetrieverConfig):
    """Config for BM25-based retrievers."""


class BaseRankerConfig(BaseModel):
    """Common config for rankers.

    If add new subconfig, it is necessary to add the corresponding instance implementation in rag.factory.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    top_n: int = Field(default=5, description="The number of top results to return.")


class LLMRankerConfig(BaseRankerConfig):
    """Config for LLM-based rankers."""

    llm: Any = Field(
        default=None,
        description="The LLM to rerank with. using Any instead of LLM, as llama_index.core.llms.LLM is pydantic.v1",
    )
