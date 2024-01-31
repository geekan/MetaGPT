from metagpt.tools.search_engine import SearchEngine


async def google_search(query: str, max_results: int = 6, **kwargs):
    """Perform a web search and retrieve search results.

    :param query: The search query.
    :param max_results: The number of search results to retrieve
    :return: The web search results in markdown format.
    """
    results = await SearchEngine(**kwargs).run(query, max_results=max_results, as_string=False)
    return "\n".join(f"{i}. [{j['title']}]({j['link']}): {j['snippet']}" for i, j in enumerate(results, 1))
