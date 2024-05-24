"""RAG Embedding Factory."""
from __future__ import annotations

from typing import Any

from llama_index.core.embeddings import BaseEmbedding
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding

from metagpt.config2 import config
from metagpt.configs.embedding_config import EmbeddingType
from metagpt.configs.llm_config import LLMType
from metagpt.rag.factories.base import GenericFactory


class RAGEmbeddingFactory(GenericFactory):
    """Create LlamaIndex Embedding with MetaGPT's embedding config."""

    def __init__(self):
        creators = {
            EmbeddingType.OPENAI: self._create_openai,
            EmbeddingType.AZURE: self._create_azure,
            EmbeddingType.GEMINI: self._create_gemini,
            EmbeddingType.OLLAMA: self._create_ollama,
            # For backward compatibility
            LLMType.OPENAI: self._create_openai,
            LLMType.AZURE: self._create_azure,
        }
        super().__init__(creators)

    def get_rag_embedding(self, key: EmbeddingType = None) -> BaseEmbedding:
        """Key is EmbeddingType."""
        return super().get_instance(key or self._resolve_embedding_type())

    def _resolve_embedding_type(self) -> EmbeddingType | LLMType:
        """Resolves the embedding type.

        If the embedding type is not specified, for backward compatibility, it checks if the LLM API type is either OPENAI or AZURE.
        Raise TypeError if embedding type not found.
        """
        if config.embedding.api_type:
            return config.embedding.api_type

        if config.llm.api_type in [LLMType.OPENAI, LLMType.AZURE]:
            return config.llm.api_type

        raise TypeError("To use RAG, please set your embedding in config2.yaml.")

    def _create_openai(self) -> OpenAIEmbedding:
        params = dict(
            api_key=config.embedding.api_key or config.llm.api_key,
            api_base=config.embedding.base_url or config.llm.base_url,
        )

        self._try_set_model_and_batch_size(params)

        return OpenAIEmbedding(**params)

    def _create_azure(self) -> AzureOpenAIEmbedding:
        params = dict(
            api_key=config.embedding.api_key or config.llm.api_key,
            azure_endpoint=config.embedding.base_url or config.llm.base_url,
            api_version=config.embedding.api_version or config.llm.api_version,
        )

        self._try_set_model_and_batch_size(params)

        return AzureOpenAIEmbedding(**params)

    def _create_gemini(self) -> GeminiEmbedding:
        params = dict(
            api_key=config.embedding.api_key,
            api_base=config.embedding.base_url,
        )

        self._try_set_model_and_batch_size(params)

        return GeminiEmbedding(**params)

    def _create_ollama(self) -> OllamaEmbedding:
        params = dict(
            base_url=config.embedding.base_url,
        )

        self._try_set_model_and_batch_size(params)

        return OllamaEmbedding(**params)

    def _try_set_model_and_batch_size(self, params: dict):
        """Set the model_name and embed_batch_size only when they are specified."""
        if config.embedding.model:
            params["model_name"] = config.embedding.model

        if config.embedding.embed_batch_size:
            params["embed_batch_size"] = config.embedding.embed_batch_size

    def _raise_for_key(self, key: Any):
        raise ValueError(f"The embedding type is currently not supported: `{type(key)}`, {key}")


get_rag_embedding = RAGEmbeddingFactory().get_rag_embedding
