from llama_index.core.llms import LLM

from metagpt.config2 import config
from metagpt.rag.factories import get_rag_llm
from metagpt.rag.factories.base import ConfigBasedFactory
from metagpt.rag.query_analysis.HyDE import HyDEQuery


class HyDEQueryTransformFactory(ConfigBasedFactory):
    """Factory for creating HyDEQueryTransform instances with LLM configuration."""

    llm: LLM = None
    hyde_config: dict = None

    def __init__(self):
        self.hyde_config = config.hyde
        self.llm = get_rag_llm()

    def create_hyde_query_transform(self) -> HyDEQuery:
        return HyDEQuery(include_original=self.hyde_config.include_original, llm=self.llm)
