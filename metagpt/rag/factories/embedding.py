"""RAG Embedding Factory."""

from llama_index.core.embeddings import BaseEmbedding
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding

from metagpt.config2 import config
from metagpt.configs.llm_config import LLMType
from metagpt.rag.factories.base import GenericFactory


class RAGEmbeddingFactory(GenericFactory):
    """Create LlamaIndex Embedding with MetaGPT's config."""

    def __init__(self):
        creators = {
            LLMType.OPENAI: self._create_openai,
            LLMType.AZURE: self._create_azure,
        }
        super().__init__(creators)

    def get_rag_embedding(self, key: LLMType = None) -> BaseEmbedding:
        """Key is LLMType, default use config.llm.api_type."""
        return super().get_instance(key or config.llm.api_type)

    def _create_openai(self):
        return OpenAIEmbedding(api_key=config.llm.api_key, api_base=config.llm.base_url)

    def _create_azure(self):
        return AzureOpenAIEmbedding(
            azure_endpoint=config.llm.base_url,
            api_key=config.llm.api_key,
            api_version=config.llm.api_version,
        )


get_rag_embedding = RAGEmbeddingFactory().get_rag_embedding
