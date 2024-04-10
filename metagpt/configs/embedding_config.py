from enum import Enum
from typing import Optional

from pydantic import field_validator

from metagpt.utils.yaml_model import YamlModel


class EmbeddingType(Enum):
    OPENAI = "openai"
    AZURE = "azure"
    GEMINI = "gemini"
    OLLAMA = "ollama"


class EmbeddingConfig(YamlModel):
    """Config for Embedding."""

    api_type: Optional[EmbeddingType] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    api_version: Optional[str] = None

    model: Optional[str] = None
    embed_batch_size: Optional[int] = None

    @field_validator("api_type", mode="before")
    @classmethod
    def check_api_type(cls, v):
        if v == "":
            return None
        return v
