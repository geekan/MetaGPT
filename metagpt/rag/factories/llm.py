"""RAG LLM Factory.

The LLM of LlamaIndex and the LLM of MG are not the same. 
"""
from llama_index.core.llms import LLM
from llama_index.llms.anthropic import Anthropic
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.llms.gemini import Gemini
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI

from metagpt.config2 import config
from metagpt.configs.llm_config import LLMType
from metagpt.rag.factories.base import GenericFactory


class RAGLLMFactory(GenericFactory):
    """Create LlamaIndex LLM with MG config."""

    def __init__(self):
        creators = {
            LLMType.OPENAI: self._create_openai,
            LLMType.AZURE: self._create_azure,
            LLMType.ANTHROPIC: self._create_anthropic,
            LLMType.GEMINI: self._create_gemini,
            LLMType.OLLAMA: self._create_ollama,
        }
        super().__init__(creators)

    def get_rag_llm(self, key: LLMType = None) -> LLM:
        """Key is LLMType, default use config.llm.api_type."""
        return super().get_instance(key or config.llm.api_type)

    def _create_openai(self):
        return OpenAI(
            api_base=config.llm.base_url,
            api_key=config.llm.api_key,
            api_version=config.llm.api_version,
            model=config.llm.model,
            max_tokens=config.llm.max_token,
            temperature=config.llm.temperature,
        )

    def _create_azure(self):
        return AzureOpenAI(
            azure_endpoint=config.llm.base_url,
            api_key=config.llm.api_key,
            api_version=config.llm.api_version,
            model=config.llm.model,
            max_tokens=config.llm.max_token,
            temperature=config.llm.temperature,
        )

    def _create_anthropic(self):
        return Anthropic(
            base_url=config.llm.base_url,
            api_key=config.llm.api_key,
            model=config.llm.model,
            max_tokens=config.llm.max_token,
            temperature=config.llm.temperature,
        )

    def _create_gemini(self):
        return Gemini(
            api_base=config.llm.base_url,
            api_key=config.llm.api_key,
            model_name=config.llm.model,
            max_tokens=config.llm.max_token,
            temperature=config.llm.temperature,
        )

    def _create_ollama(self):
        return Ollama(base_url=config.llm.base_url, model=config.llm.model, temperature=config.llm.temperature)


get_rag_llm = RAGLLMFactory().get_rag_llm
