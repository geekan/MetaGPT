"""RAG schemas."""

from pathlib import Path
from typing import Any, Union

from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.indices.base import BaseIndex
from llama_index.core.schema import TextNode
from pydantic import BaseModel, ConfigDict, Field

from metagpt.rag.interface import RAGObject


class BaseRetrieverConfig(BaseModel):
    """Common config for retrievers.

    If add new subconfig, it is necessary to add the corresponding instance implementation in rag.factories.retriever.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    similarity_top_k: int = Field(default=5, description="Number of top-k similar results to return during retrieval.")


class IndexRetrieverConfig(BaseRetrieverConfig):
    """Config for Index-basd retrievers."""

    index: BaseIndex = Field(default=None, description="Index for retriver.")


class FAISSRetrieverConfig(IndexRetrieverConfig):
    """Config for FAISS-based retrievers."""

    dimensions: int = Field(default=1536, description="Dimensionality of the vectors for FAISS index construction.")


class BM25RetrieverConfig(IndexRetrieverConfig):
    """Config for BM25-based retrievers."""


class ChromaRetrieverConfig(IndexRetrieverConfig):
    """Config for Chroma-based retrievers."""

    persist_path: Union[str, Path] = Field(default="./chroma_db", description="The directory to save data.")
    collection_name: str = Field(default="metagpt", description="The name of the collection.")


class BaseRankerConfig(BaseModel):
    """Common config for rankers.

    If add new subconfig, it is necessary to add the corresponding instance implementation in rag.factories.ranker.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    top_n: int = Field(default=5, description="The number of top results to return.")


class LLMRankerConfig(BaseRankerConfig):
    """Config for LLM-based rankers."""

    llm: Any = Field(
        default=None,
        description="The LLM to rerank with. using Any instead of LLM, as llama_index.core.llms.LLM is pydantic.v1.",
    )


class BaseIndexConfig(BaseModel):
    """Common config for index.

    If add new subconfig, it is necessary to add the corresponding instance implementation in rag.factories.index.
    """

    persist_path: Union[str, Path] = Field(description="The directory of saved data.")


class VectorIndexConfig(BaseIndexConfig):
    """Config for vector-based index."""

    embed_model: BaseEmbedding = Field(default=None, description="Embed model.")


class FAISSIndexConfig(VectorIndexConfig):
    """Config for faiss-based index."""


class ChromaIndexConfig(VectorIndexConfig):
    """Config for chroma-based index."""

    collection_name: str = Field(default="metagpt", description="The name of the collection.")


class ObjectNodeMetadata(BaseModel):
    """Metadata of ObjectNode."""

    is_obj: bool = Field(default=True)
    obj_dict: dict = Field(..., description="Inplement rag.interface.RAGObject.model_dump(), e.g. obj.model_dump()")
    obj_cls_name: str = Field(..., description="The class name of object, e.g. obj.__class__.__name__")
    obj_mod_name: str = Field(..., description="The module name of class, e.g. obj.__class__.__module__")


class ObjectNode(TextNode):
    """RAG add object."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.excluded_llm_metadata_keys = list(ObjectNodeMetadata.model_fields.keys())

    @staticmethod
    def get_obj_metadata(obj: RAGObject) -> dict:
        metadata = ObjectNodeMetadata(
            obj_dict=obj.model_dump(), obj_cls_name=obj.__class__.__name__, obj_mod_name=obj.__class__.__module__
        )
        return metadata.model_dump()
