"""RAG LLM
The LLM of LlamaIndex and the LLM of MG are not the same. 
"""
from llama_index.llms import OpenAI

from metagpt.config2 import config


def get_default_llm() -> OpenAI:
    """OpenAI"""
    return OpenAI(api_base=config.llm.base_url, api_key=config.llm.api_key, model=config.llm.model)
