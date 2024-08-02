"""Enhancing question-answering capabilities through search engine augmentation."""

from __future__ import annotations

import json

from pydantic import Field, model_validator

from metagpt.actions import Action
from metagpt.actions.research import CollectLinks, WebBrowseAndSummarize
from metagpt.logs import logger
from metagpt.tools.web_browser_engine import WebBrowserEngine
from metagpt.utils.common import CodeParser

REWRITE_QUERY_PROMPT = """
Role: You are a highly efficient assistant that provide a better search query for web search engine to answer the given question.

I will provide you with a question. Your task is to provide a better search query for web search engine.

## Context
### Question
{q}

## Format Example
```json
{{
    "query": "the better search query for web search engine.",
}}
```

## Instructions
- Understand the question given by the user.
- Provide a better search query for web search engine to answer the given question, your answer must be written in the same language as the question.
- When rewriting, if you are unsure of the specific time, do not include the time.

## Constraint
Format: Just print the result in json format like **Format Example**.

## Action
Follow **Instructions**, generate output and make sure it follows the **Constraint**.
"""

SEARCH_ENHANCED_QA_SYSTEM_PROMPT = """
You are a large language AI assistant built by MGX. You are given a user question, and please write clean, concise and accurate answer to the question. You will be given a set of related contexts to the question, each starting with a reference number like [[citation:x]], where x is a number. Please use the context.

Your answer must be correct, accurate and written by an expert using an unbiased and professional tone. Please limit to 1024 tokens. Do not give any information that is not related to the question, and do not repeat. Say "information is missing on" followed by the related topic, if the given context do not provide sufficient information. Do not include [citation] in your anwser.

Here are the set of contexts:

{context}

Remember, don't blindly repeat the contexts verbatim. And here is the user question:
"""


class SearchEnhancedQA(Action):
    """Enhancing question-answering capabilities through search engine augmentation."""

    name: str = "SearchEnhancedQA"
    desc: str = "Integrating search engine results to anwser the question."

    collect_links_action: CollectLinks = Field(
        default=CollectLinks(), description="Action to collect relevant links from a search engine."
    )
    web_browse_and_summarize_action: WebBrowseAndSummarize = Field(
        default=None,
        description="Action to explore the web and provide summaries of articles and webpages.",
    )
    per_page_timeout: float = Field(
        default=10, description="The maximum time for fetching a single page is in seconds. Defaults to 10s."
    )
    java_script_enabled: bool = Field(
        default=False, description="Whether or not to enable JavaScript in the web browser context. Defaults to False."
    )

    @model_validator(mode="after")
    def initialize(self):
        if self.web_browse_and_summarize_action is None:
            self.web_browser_engine = WebBrowserEngine.from_browser_config(
                self.config.browser, proxy=self.config.proxy, java_script_enabled=self.java_script_enabled
            )

            self.web_browse_and_summarize_action = WebBrowseAndSummarize(web_browser_engine=self.web_browser_engine)

        return self

    async def run(self, query: str, rewrite_query: bool = True) -> str:
        """Answer a query by leveraging web search results.

        Args:
            query (str): The original user query.
            rewrite_query (bool): Whether to rewrite the query for better web search results. Defaults to True.

        Returns:
            str: A detailed answer based on web search results.

        Raises:
            ValueError: If the query is invalid.
        """

        self._validate_query(query)

        processed_query = await self._process_query(query, rewrite_query)
        context = await self._build_context(processed_query)

        return await self._generate_answer(processed_query, context)

    def _validate_query(self, query: str) -> None:
        """Validate the input query.

        Args:
            query (str): The query to validate.

        Raises:
            ValueError: If the query is invalid.
        """

        if not query.strip():
            raise ValueError("Query cannot be empty or contain only whitespace.")

    async def _process_query(self, query: str, should_rewrite: bool) -> str:
        """Process the query, optionally rewriting it."""

        if should_rewrite:
            return await self._rewrite_query(query)

        return query

    async def _rewrite_query(self, query: str) -> str:
        """Write a better search query for web search engine.

        If the rewrite process fails, the original query is returned.

        Args:
            query (str): The original search query.

        Returns:
            str: The rewritten query if successful, otherwise the original query.
        """

        prompt = REWRITE_QUERY_PROMPT.format(q=query)

        try:
            resp = await self._aask(prompt)
            rewritten_query = self._extract_rewritten_query(resp)

            logger.info(f"Query rewritten: '{query}' -> '{rewritten_query}'")
            return rewritten_query
        except Exception as e:
            logger.warning(f"Query rewrite failed. Returning original query. Error: {e}")
            return query

    def _extract_rewritten_query(self, response: str) -> str:
        """Extract the rewritten query from the LLM's JSON response."""

        resp_json = json.loads(CodeParser.parse_code(response, lang="json"))
        return resp_json["query"]

    async def _build_context(self, query: str) -> str:
        """Construct a context string from web search citations.

        Args:
            query (str): The search query.

        Returns:
            str: Formatted context with numbered citations.
        """

        citations = await self._search_citations(query)
        context = "\n\n".join([f"[[citation:{i+1}]] {c}" for i, c in enumerate(citations)])

        return context

    async def _search_citations(self, query: str) -> list[str]:
        """Perform web search and summarize relevant content.

        Args:
            query (str): The search query.

        Returns:
            list[str]: Summaries of relevant web content.
        """

        relevant_urls = await self._collect_relevant_links(query)
        if not relevant_urls:
            logger.warning(f"No relevant URLs found for query: {query}")
            return []

        logger.info(f"The Relevant links are: {relevant_urls}")

        web_summaries = await self._summarize_web_content(relevant_urls, query)
        if not web_summaries:
            logger.warning(f"No summaries generated for query: {query}")
            return []

        citations = list(web_summaries.values())

        return citations

    async def _collect_relevant_links(self, query: str) -> list[str]:
        """Search and rank URLs relevant to the query.

        Args:
            query (str): The search query.

        Returns:
            list[str]: Ranked list of relevant URLs.
        """

        return await self.collect_links_action._search_and_rank_urls(topic=query, query=query)

    async def _summarize_web_content(self, urls: list[str], query: str) -> dict[str, str]:
        """Fetch and summarize content from given URLs.

        Args:
            urls (list[str]): List of URLs to summarize.
            query (str): The original query for context.

        Returns:
            dict[str, str]: Mapping of URLs to their summaries.
        """

        return await self.web_browse_and_summarize_action.run(
            *urls, query=query, use_concurrent_summarization=True, per_page_timeout=self.per_page_timeout
        )

    async def _generate_answer(self, query: str, context: str) -> str:
        """Generate an answer using the query and context.

        Args:
            query (str): The user's question.
            context (str): Relevant information from web search.

        Returns:
            str: Generated answer based on the context.
        """

        system_prompt = SEARCH_ENHANCED_QA_SYSTEM_PROMPT.format(context=context)

        return await self._aask(query, [system_prompt])
