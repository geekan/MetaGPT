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
    """Config for Embedding.

    Examples:
    ---------
    api_type: "openai"
    api_key: "YOU_API_KEY"
    dimensions: "YOUR_MODEL_DIMENSIONS"

    api_type: "azure"
    api_key: "YOU_API_KEY"
    base_url: "YOU_BASE_URL"
    api_version: "YOU_API_VERSION"
    dimensions: "YOUR_MODEL_DIMENSIONS"

    api_type: "gemini"
    api_key: "YOU_API_KEY"

    api_type: "ollama"
    base_url: "YOU_BASE_URL"
    model: "YOU_MODEL"
    dimensions: "YOUR_MODEL_DIMENSIONS"
    """

    api_type: Optional[EmbeddingType] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    api_version: Optional[str] = None

    model: Optional[str] = None
    embed_batch_size: Optional[int] = None
    dimensions: Optional[int] = None  # output dimension of embedding model

    @field_validator("api_type", mode="before")
    @classmethod
    def check_api_type(cls, v):
        if v == "":
            return None
        return v
