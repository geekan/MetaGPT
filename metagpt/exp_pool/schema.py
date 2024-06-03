from pydantic import BaseModel, Field
from llama_index.core.schema import TextNode


class Experience(BaseModel):
    req: str = Field(..., description="")
    resp: str = Field(..., description="")

    def rag_key(self):
        return self.req


class ExperienceNodeMetadata(BaseModel):
    """Metadata of ExperienceNode."""

    resp: str = Field(..., description="")


class ExperienceNode(TextNode):
    """ExperienceNode for RAG."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.excluded_llm_metadata_keys = list(ExperienceNodeMetadata.model_fields.keys())
        self.excluded_embed_metadata_keys = self.excluded_llm_metadata_keys
