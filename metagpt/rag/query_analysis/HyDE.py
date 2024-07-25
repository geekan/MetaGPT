from typing import Dict

from llama_index.core.indices.query.query_transform import HyDEQueryTransform
from llama_index.core.llms import LLM
from llama_index.core.schema import QueryBundle

from metagpt.config2 import config
from metagpt.logs import logger
from metagpt.rag.factories import get_rag_llm
from metagpt.rag.factories.base import ConfigBasedFactory


class HyDEQuery(HyDEQueryTransform):
    def _run(self, query_bundle: QueryBundle, metadata: Dict) -> QueryBundle:
        logger.info(f"{'#' * 5} running HyDEQuery... {'#' * 5}")
        query_str = query_bundle.query_str

        hypothetical_doc = self._llm.predict(self._hyde_prompt, context_str=query_str)

        embedding_strs = [hypothetical_doc]

        if self._include_original:
            embedding_strs.extend(query_bundle.embedding_strs)
        logger.info(f" Hypothetical doc:{embedding_strs} ")

        return QueryBundle(
            query_str=query_str,
            custom_embedding_strs=embedding_strs,
        )


class HyDEQueryTransformFactory(ConfigBasedFactory):
    """Factory for creating HyDEQueryTransform instances with LLM configuration."""

    llm: LLM = None
    hyde_config: dict = None

    def __init__(self):
        self.hyde_config = config.hyde
        self.llm = get_rag_llm()

    def create_hyde_query_transform(self) -> HyDEQuery:
        return HyDEQuery(include_original=self.hyde_config.include_original, llm=self.llm)
