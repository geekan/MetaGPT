#!/usr/bin/env python

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Callable, Coroutine, Optional, Union

from pydantic import TypeAdapter, model_validator

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.tools.search_engine import SearchEngine
from metagpt.tools.web_browser_engine import WebBrowserEngine
from metagpt.utils.common import OutputParser
from metagpt.utils.parse_html import WebPage
from metagpt.utils.text import generate_prompt_chunk, reduce_message_length

LANG_PROMPT = "Please respond in {language}."

RESEARCH_BASE_SYSTEM = """You are an AI critical thinker research assistant. Your sole purpose is to write well \
written, critically acclaimed, objective and structured reports on the given text."""

RESEARCH_TOPIC_SYSTEM = "You are an AI researcher assistant, and your research topic is:\n#TOPIC#\n{topic}"

SEARCH_TOPIC_PROMPT = """Please provide up to 2 necessary keywords related to your research topic for Google search. \
Your response must be in JSON format, for example: ["keyword1", "keyword2"]."""

SUMMARIZE_SEARCH_PROMPT = """### Requirements
1. The keywords related to your research topic and the search results are shown in the "Search Result Information" section.
2. Provide up to {decomposition_nums} queries related to your research topic base on the search results.
3. Please respond in the following JSON format: ["query1", "query2", "query3", ...].

### Search Result Information
{search_results}
"""

COLLECT_AND_RANKURLS_PROMPT = """### Topic
{topic}
### Query
{query}

### The online search results
{results}

### Requirements
Please remove irrelevant search results that are not related to the query or topic.
If the query is time-sensitive or specifies a certain time frame, please also remove search results that are outdated or outside the specified time frame. Notice that the current time is {time_stamp}.
Then, sort the remaining search results based on the link credibility. If two results have equal credibility, prioritize them based on the relevance.
Provide the ranked results' indices in JSON format, like [0, 1, 3, 4, ...], without including other words.
"""

WEB_BROWSE_AND_SUMMARIZE_PROMPT = """### Requirements
1. Utilize the text in the "Reference Information" section to respond to the question "{query}".
2. If the question cannot be directly answered using the text, but the text is related to the research topic, please provide \
a comprehensive summary of the text.
3. If the text is entirely unrelated to the research topic, please reply with a simple text "Not relevant."
4. Include all relevant factual information, numbers, statistics, etc., if available.

### Reference Information
{content}
"""


CONDUCT_RESEARCH_PROMPT = """### Reference Information
{content}

### Requirements
Please provide a detailed research report in response to the following topic: "{topic}", using the information provided \
above. The report must meet the following requirements:

- Focus on directly addressing the chosen topic.
- Ensure a well-structured and in-depth presentation, incorporating relevant facts and figures where available.
- Present data and findings in an intuitive manner, utilizing feature comparative tables, if applicable.
- The report should have a minimum word count of 2,000 and be formatted with Markdown syntax following APA style guidelines.
- Include all source URLs in APA format at the end of the report.
"""


class CollectLinks(Action):
    """Action class to collect links from a search engine."""

    name: str = "CollectLinks"
    i_context: Optional[str] = None
    desc: str = "Collect links from a search engine."
    search_func: Optional[Any] = None
    search_engine: Optional[SearchEngine] = None
    rank_func: Optional[Callable[[list[str]], None]] = None

    @model_validator(mode="after")
    def validate_engine_and_run_func(self):
        if self.search_engine is None:
            self.search_engine = SearchEngine.from_search_config(self.config.search, proxy=self.config.proxy)
        return self

    async def run(
        self,
        topic: str,
        decomposition_nums: int = 4,
        url_per_query: int = 4,
        system_text: str | None = None,
    ) -> dict[str, list[str]]:
        """Run the action to collect links.

        Args:
            topic: The research topic.
            decomposition_nums: The number of search questions to generate.
            url_per_query: The number of URLs to collect per search question.
            system_text: The system text.

        Returns:
            A dictionary containing the search questions as keys and the collected URLs as values.
        """
        system_text = system_text if system_text else RESEARCH_TOPIC_SYSTEM.format(topic=topic)
        keywords = await self._aask(SEARCH_TOPIC_PROMPT, [system_text])
        try:
            keywords = OutputParser.extract_struct(keywords, list)
            keywords = TypeAdapter(list[str]).validate_python(keywords)
        except Exception as e:
            logger.exception(f"fail to get keywords related to the research topic '{topic}' for {e}")
            keywords = [topic]
        results = await asyncio.gather(*(self.search_engine.run(i, as_string=False) for i in keywords))

        def gen_msg():
            while True:
                search_results = "\n".join(
                    f"#### Keyword: {i}\n Search Result: {j}\n" for (i, j) in zip(keywords, results)
                )
                prompt = SUMMARIZE_SEARCH_PROMPT.format(
                    decomposition_nums=decomposition_nums, search_results=search_results
                )
                yield prompt
                remove = max(results, key=len)
                remove.pop()
                if len(remove) == 0:
                    break

        model_name = self.config.llm.model
        prompt = reduce_message_length(gen_msg(), model_name, system_text, self.config.llm.max_token)
        logger.debug(prompt)
        queries = await self._aask(prompt, [system_text])
        try:
            queries = OutputParser.extract_struct(queries, list)
            queries = TypeAdapter(list[str]).validate_python(queries)
        except Exception as e:
            logger.exception(f"fail to break down the research question due to {e}")
            queries = keywords
        ret = {}
        for query in queries:
            ret[query] = await self._search_and_rank_urls(topic, query, url_per_query)
        return ret

    async def _search_and_rank_urls(
        self, topic: str, query: str, num_results: int = 4, max_num_results: int = None
    ) -> list[str]:
        """Search and rank URLs based on a query.

        Args:
            topic: The research topic.
            query: The search query.
            num_results: The number of URLs to collect.
            max_num_results: The max number of URLs to collect.

        Returns:
            A list of ranked URLs.
        """
        max_results = max_num_results or max(num_results * 2, 6)
        results = await self._search_urls(query, max_results=max_results)
        if len(results) == 0:
            return []
        _results = "\n".join(f"{i}: {j}" for i, j in zip(range(max_results), results))
        time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt = COLLECT_AND_RANKURLS_PROMPT.format(topic=topic, query=query, results=_results, time_stamp=time_stamp)
        logger.debug(prompt)
        indices = await self._aask(prompt)
        try:
            indices = OutputParser.extract_struct(indices, list)
            assert all(isinstance(i, int) for i in indices)
        except Exception as e:
            logger.exception(f"fail to rank results for {e}")
            indices = list(range(max_results))
        results = [results[i] for i in indices]
        if self.rank_func:
            results = self.rank_func(results)
        return [i["link"] for i in results[:num_results]]

    async def _search_urls(self, query: str, max_results: int) -> list[dict[str, str]]:
        """Use search_engine to get urls.

        Returns:
            e.g. [{"title": "...", "link": "...", "snippet", "..."}]
        """

        return await self.search_engine.run(query, max_results=max_results, as_string=False)


class WebBrowseAndSummarize(Action):
    """Action class to explore the web and provide summaries of articles and webpages."""

    name: str = "WebBrowseAndSummarize"
    i_context: Optional[str] = None
    desc: str = "Explore the web and provide summaries of articles and webpages."
    browse_func: Union[Callable[[list[str]], None], None] = None
    web_browser_engine: Optional[WebBrowserEngine] = None

    @model_validator(mode="after")
    def validate_engine_and_run_func(self):
        if self.web_browser_engine is None:
            self.web_browser_engine = WebBrowserEngine.from_browser_config(
                self.config.browser,
                browse_func=self.browse_func,
                proxy=self.config.proxy,
            )
        return self

    async def run(
        self,
        url: str,
        *urls: str,
        query: str,
        system_text: str = RESEARCH_BASE_SYSTEM,
        use_concurrent_summarization: bool = False,
        per_page_timeout: Optional[float] = None,
    ) -> dict[str, str]:
        """Run the action to browse the web and provide summaries.

        Args:
            url: The main URL to browse.
            urls: Additional URLs to browse.
            query: The research question.
            system_text: The system text.
            use_concurrent_summarization: Whether to concurrently summarize the content of the webpage by LLM.
            per_page_timeout: The maximum time for fetching a single page in seconds.

        Returns:
            A dictionary containing the URLs as keys and their summaries as values.
        """
        contents = await self._fetch_web_contents(url, *urls, per_page_timeout=per_page_timeout)

        all_urls = [url] + list(urls)
        summarize_tasks = [self._summarize_content(content, query, system_text) for content in contents]
        summaries = await self._execute_summarize_tasks(summarize_tasks, use_concurrent_summarization)
        result = {url: summary for url, summary in zip(all_urls, summaries) if summary}

        return result

    async def _fetch_web_contents(
        self, url: str, *urls: str, per_page_timeout: Optional[float] = None
    ) -> list[WebPage]:
        """Fetch web contents from given URLs."""

        contents = await self.web_browser_engine.run(url, *urls, per_page_timeout=per_page_timeout)

        return [contents] if not urls else contents

    async def _summarize_content(self, page: WebPage, query: str, system_text: str) -> str:
        """Summarize web content."""
        try:
            prompt_template = WEB_BROWSE_AND_SUMMARIZE_PROMPT.format(query=query, content="{}")

            content = page.inner_text

            if self._is_content_invalid(content):
                logger.warning(f"Invalid content detected for URL {page.url}: {content[:10]}...")
                return None

            chunk_summaries = []
            for prompt in generate_prompt_chunk(content, prompt_template, self.llm.model, system_text, 4096):
                logger.debug(prompt)
                summary = await self._aask(prompt, [system_text])
                if summary == "Not relevant.":
                    continue
                chunk_summaries.append(summary)

            if not chunk_summaries:
                return None

            if len(chunk_summaries) == 1:
                return chunk_summaries[0]

            content = "\n".join(chunk_summaries)
            prompt = WEB_BROWSE_AND_SUMMARIZE_PROMPT.format(query=query, content=content)
            summary = await self._aask(prompt, [system_text])
            return summary
        except Exception as e:
            logger.error(f"Error summarizing content: {e}")
            return None

    def _is_content_invalid(self, content: str) -> bool:
        """Check if the content is invalid based on specific starting phrases."""

        invalid_starts = ["Fail to load page", "Access Denied"]

        return any(content.strip().startswith(phrase) for phrase in invalid_starts)

    async def _execute_summarize_tasks(self, tasks: list[Coroutine[Any, Any, str]], use_concurrent: bool) -> list[str]:
        """Execute summarize tasks either concurrently or sequentially."""

        if use_concurrent:
            return await asyncio.gather(*tasks)

        return [await task for task in tasks]


class ConductResearch(Action):
    """Action class to conduct research and generate a research report."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def run(
        self,
        topic: str,
        content: str,
        system_text: str = RESEARCH_BASE_SYSTEM,
    ) -> str:
        """Run the action to conduct research and generate a research report.

        Args:
            topic: The research topic.
            content: The content for research.
            system_text: The system text.

        Returns:
            The generated research report.
        """
        prompt = CONDUCT_RESEARCH_PROMPT.format(topic=topic, content=content)
        logger.debug(prompt)
        self.llm.auto_max_tokens = True
        return await self._aask(prompt, [system_text])


def get_research_system_text(topic: str, language: str):
    """Get the system text for conducting research.

    Args:
        topic: The research topic.
        language: The language for the system text.

    Returns:
        The system text for conducting research.
    """
    return " ".join((RESEARCH_TOPIC_SYSTEM.format(topic=topic), LANG_PROMPT.format(language=language)))
