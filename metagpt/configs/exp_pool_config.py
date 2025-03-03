from enum import Enum

from pydantic import Field

from metagpt.utils.yaml_model import YamlModel


class ExperiencePoolRetrievalType(Enum):
    BM25 = "bm25"
    CHROMA = "chroma"


class ExperiencePoolConfig(YamlModel):
    enabled: bool = Field(
        default=False,
        description="Flag to enable or disable the experience pool. When disabled, both reading and writing are ineffective.",
    )
    enable_read: bool = Field(default=False, description="Enable to read from experience pool.")
    enable_write: bool = Field(default=False, description="Enable to write to experience pool.")
    persist_path: str = Field(default=".chroma_exp_data", description="The persist path for experience pool.")
    retrieval_type: ExperiencePoolRetrievalType = Field(
        default=ExperiencePoolRetrievalType.BM25, description="The retrieval type for experience pool."
    )
    use_llm_ranker: bool = Field(default=True, description="Use LLM Reranker to get better result.")
    collection_name: str = Field(default="experience_pool", description="The collection name in chromadb")
