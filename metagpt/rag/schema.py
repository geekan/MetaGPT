"""RAG schemas."""

from pathlib import Path
from typing import Any, ClassVar, Literal, Optional, Union

from chromadb.api.types import CollectionMetadata
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.indices.base import BaseIndex
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator

from metagpt.config2 import config
from metagpt.configs.embedding_config import EmbeddingType
from metagpt.logs import logger
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

    dimensions: int = Field(default=0, description="Dimensionality of the vectors for FAISS index construction.")

    _embedding_type_to_dimensions: ClassVar[dict[EmbeddingType, int]] = {
        EmbeddingType.GEMINI: 768,
        EmbeddingType.OLLAMA: 4096,
    }

    @model_validator(mode="after")
    def check_dimensions(self):
        if self.dimensions == 0:
            self.dimensions = config.embedding.dimensions or self._embedding_type_to_dimensions.get(
                config.embedding.api_type, 1536
            )
            if not config.embedding.dimensions and config.embedding.api_type not in self._embedding_type_to_dimensions:
                logger.warning(
                    f"You didn't set dimensions in config when using {config.embedding.api_type}, default to 1536"
                )

        return self


class BM25RetrieverConfig(IndexRetrieverConfig):
    """Config for BM25-based retrievers."""

    _no_embedding: bool = PrivateAttr(default=True)


class ChromaRetrieverConfig(IndexRetrieverConfig):
    """Config for Chroma-based retrievers."""

    persist_path: Union[str, Path] = Field(default="./chroma_db", description="The directory to save data.")
    collection_name: str = Field(default="metagpt", description="The name of the collection.")
    metadata: Optional[CollectionMetadata] = Field(
        default=None, description="Optional metadata to associate with the collection"
    )


class ElasticsearchStoreConfig(BaseModel):
    index_name: str = Field(default="metagpt", description="Name of the Elasticsearch index.")
    es_url: str = Field(default=None, description="Elasticsearch URL.")
    es_cloud_id: str = Field(default=None, description="Elasticsearch cloud ID.")
    es_api_key: str = Field(default=None, description="Elasticsearch API key.")
    es_user: str = Field(default=None, description="Elasticsearch username.")
    es_password: str = Field(default=None, description="Elasticsearch password.")
    batch_size: int = Field(default=200, description="Batch size for bulk indexing.")
    distance_strategy: str = Field(default="COSINE", description="Distance strategy to use for similarity search.")


class ElasticsearchRetrieverConfig(IndexRetrieverConfig):
    """Config for Elasticsearch-based retrievers. Support both vector and text."""

    store_config: ElasticsearchStoreConfig = Field(..., description="ElasticsearchStore config.")
    vector_store_query_mode: VectorStoreQueryMode = Field(
        default=VectorStoreQueryMode.DEFAULT, description="default is vector query."
    )


class ElasticsearchKeywordRetrieverConfig(ElasticsearchRetrieverConfig):
    """Config for Elasticsearch-based retrievers. Support text only."""

    _no_embedding: bool = PrivateAttr(default=True)
    vector_store_query_mode: Literal[VectorStoreQueryMode.TEXT_SEARCH] = Field(
        default=VectorStoreQueryMode.TEXT_SEARCH, description="text query only."
    )


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


class ColbertRerankConfig(BaseRankerConfig):
    model: str = Field(default="colbert-ir/colbertv2.0", description="Colbert model name.")
    device: str = Field(default="cpu", description="Device to use for sentence transformer.")
    keep_retrieval_score: bool = Field(default=False, description="Whether to keep the retrieval score in metadata.")


class CohereRerankConfig(BaseRankerConfig):
    model: str = Field(default="rerank-english-v3.0")
    api_key: str = Field(default="YOUR_COHERE_API")


class BGERerankConfig(BaseRankerConfig):
    model: str = Field(default="BAAI/bge-reranker-large", description="BAAI Reranker model name.")
    use_fp16: bool = Field(default=True, description="Whether to use fp16 for inference.")


class ObjectRankerConfig(BaseRankerConfig):
    field_name: str = Field(..., description="field name of the object, field's value must can be compared.")
    order: Literal["desc", "asc"] = Field(default="desc", description="the direction of order.")


class BaseIndexConfig(BaseModel):
    """Common config for index.

    If add new subconfig, it is necessary to add the corresponding instance implementation in rag.factories.index.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    persist_path: Union[str, Path] = Field(description="The directory of saved data.")


class VectorIndexConfig(BaseIndexConfig):
    """Config for vector-based index."""

    embed_model: BaseEmbedding = Field(default=None, description="Embed model.")


class FAISSIndexConfig(VectorIndexConfig):
    """Config for faiss-based index."""


class ChromaIndexConfig(VectorIndexConfig):
    """Config for chroma-based index."""

    collection_name: str = Field(default="metagpt", description="The name of the collection.")
    metadata: Optional[CollectionMetadata] = Field(
        default=None, description="Optional metadata to associate with the collection"
    )


class BM25IndexConfig(BaseIndexConfig):
    """Config for bm25-based index."""

    _no_embedding: bool = PrivateAttr(default=True)


class ElasticsearchIndexConfig(VectorIndexConfig):
    """Config for es-based index."""

    store_config: ElasticsearchStoreConfig = Field(..., description="ElasticsearchStore config.")
    persist_path: Union[str, Path] = ""


class ElasticsearchKeywordIndexConfig(ElasticsearchIndexConfig):
    """Config for es-based index. no embedding."""

    _no_embedding: bool = PrivateAttr(default=True)


class ObjectNodeMetadata(BaseModel):
    """Metadata of ObjectNode."""

    is_obj: bool = Field(default=True)
    obj: Any = Field(default=None, description="When rag retrieve, will reconstruct obj from obj_json")
    obj_json: str = Field(..., description="The json of object, e.g. obj.model_dump_json()")
    obj_cls_name: str = Field(..., description="The class name of object, e.g. obj.__class__.__name__")
    obj_mod_name: str = Field(..., description="The module name of class, e.g. obj.__class__.__module__")


class ObjectNode(TextNode):
    """RAG add object."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.excluded_llm_metadata_keys = list(ObjectNodeMetadata.model_fields.keys())
        self.excluded_embed_metadata_keys = self.excluded_llm_metadata_keys

    @staticmethod
    def get_obj_metadata(obj: RAGObject) -> dict:
        metadata = ObjectNodeMetadata(
            obj_json=obj.model_dump_json(), obj_cls_name=obj.__class__.__name__, obj_mod_name=obj.__class__.__module__
        )

        return metadata.model_dump()
