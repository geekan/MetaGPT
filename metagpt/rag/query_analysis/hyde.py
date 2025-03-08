from typing import Any, Dict, Optional

from llama_index.core.indices.query.query_transform import HyDEQueryTransform
from llama_index.core.prompts import BasePromptTemplate
from llama_index.core.prompts.default_prompts import DEFAULT_HYDE_PROMPT
from llama_index.core.schema import QueryBundle
from llama_index.core.service_context_elements.llm_predictor import LLMPredictorType

from metagpt.config2 import config
from metagpt.logs import logger
from metagpt.rag.factories import get_rag_llm


class HyDEQuery(HyDEQueryTransform):
    def __init__(
        self,
        llm: Optional[LLMPredictorType] = None,
        hyde_prompt: Optional[BasePromptTemplate] = None,
        include_original: Optional[bool] = None,
    ) -> None:
        """Initialize the HyDEQueryTransform class with optional parameters.

        Args:
            llm (Optional[LLMPredictorType]): An LLM (Language Learning Model) used for generating
                hypothetical documents. If not provided, defaults to rag_llm.
            hyde_prompt (Optional[BasePromptTemplate]): Custom prompt template for HyDE.
                If not provided, the default prompt is used.
            include_original (Optional[bool]): Flag to include the original query string in the output.
                If not provided, the setting is fetched from config or defaults to True.
        """
        # Set LLM, using a default if not provided
        self._llm = llm or get_rag_llm()
        # Set the prompt template, using a default if not provided
        self._hyde_prompt = hyde_prompt or DEFAULT_HYDE_PROMPT
        # Set the flag to include the original query, fetching from config if not provided
        if include_original is not None:
            self._include_original = include_original
        else:
            try:
                self._include_original = config.rag.query_analysis.hyde
            except AttributeError:
                self._include_original = True

    def _run(self, query_bundle: QueryBundle, metadata: Dict[str, Any]) -> QueryBundle:
        """Process the query bundle to include hypothetical document embeddings.

        Args:
            query_bundle (QueryBundle): The original query bundle containing query information.
            metadata (Dict[str, Any]): Additional metadata for processing.

        Returns:
            QueryBundle: Updated query bundle with additional hypothetical document embeddings.
        """
        # Log the operation
        logger.info(f"{'#' * 5} Running HyDEQuery... {'#' * 5}")
        # Generate the hypothetical document using the LLM and prompt
        query_str = query_bundle.query_str
        hypothetical_doc = self._llm.predict(self._hyde_prompt, context_str=query_str)
        embedding_strs = [hypothetical_doc]
        # Include the original query strings if specified
        if self._include_original:
            embedding_strs.extend(query_bundle.embedding_strs)

        return QueryBundle(query_str=query_str, custom_embedding_strs=embedding_strs)
