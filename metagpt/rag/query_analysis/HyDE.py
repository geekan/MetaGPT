from typing import Dict

from llama_index.core.indices.query.query_transform import HyDEQueryTransform
from llama_index.core.schema import QueryBundle

from metagpt.logs import logger


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
