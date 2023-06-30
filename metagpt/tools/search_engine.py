#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/6 20:15
@Author  : alexanderwu
@File    : search_engine.py
"""
from __future__ import annotations

import json

from metagpt.logs import logger
from duckduckgo_search import ddg

from metagpt.config import Config
from metagpt.tools.search_engine_serpapi import SerpAPIWrapper

config = Config()
from metagpt.tools import SearchEngineType


class SearchEngine:
    """
    TODO: 合入Google Search 并进行反代
    注：这里Google需要挂Proxifier或者类似全局代理
    - DDG: https://pypi.org/project/duckduckgo-search/
    - GOOGLE: https://programmablesearchengine.google.com/controlpanel/overview?cx=63f9de531d0e24de9
    """
    def __init__(self, engine=None, run_func=None):
        self.config = Config()
        self.run_func = run_func
        self.engine = engine or self.config.search_engine

    @classmethod
    def run_google(cls, query, max_results=8):
        # results = ddg(query, max_results=max_results)
        results = google_official_search(query, num_results=max_results)
        logger.info(results)
        return results

    async def run(self, query, max_results=8):
        if self.engine == SearchEngineType.SERPAPI_GOOGLE:
            api = SerpAPIWrapper()
            rsp = await api.run(query)
        elif self.engine == SearchEngineType.DIRECT_GOOGLE:
            rsp = SearchEngine.run_google(query, max_results)
        elif self.engine == SearchEngineType.CUSTOM_ENGINE:
            rsp = self.run_func(query)
        else:
            raise NotImplementedError
        return rsp


def google_official_search(query: str, num_results: int = 8, focus=['snippet', 'link', 'title']) -> dict | list[dict]:
    """Return the results of a Google search using the official Google API

    Args:
        query (str): The search query.
        num_results (int): The number of results to return.

    Returns:
        str: The results of the search.
    """

    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    try:
        api_key = config.google_api_key
        custom_search_engine_id = config.google_cse_id

        service = build("customsearch", "v1", developerKey=api_key)

        result = (
            service.cse()
            .list(q=query, cx=custom_search_engine_id, num=num_results)
            .execute()
        )

        # Extract the search result items from the response
        search_results = result.get("items", [])

        # Create a list of only the URLs from the search results
        search_results_details = [{i: j for i, j in item_dict.items() if i in focus} for item_dict in search_results]

    except HttpError as e:
        # Handle errors in the API call
        error_details = json.loads(e.content.decode())

        # Check if the error is related to an invalid or missing API key
        if error_details.get("error", {}).get(
            "code"
        ) == 403 and "invalid API key" in error_details.get("error", {}).get(
            "message", ""
        ):
            return "Error: The provided Google API key is invalid or missing."
        else:
            return f"Error: {e}"
    # google_result can be a list or a string depending on the search results

    # Return the list of search result URLs
    return search_results_details


def safe_google_results(results: str | list) -> str:
    """
        Return the results of a google search in a safe format.

    Args:
        results (str | list): The search results.

    Returns:
        str: The results of the search.
    """
    if isinstance(results, list):
        safe_message = json.dumps(
            # FIXME: # .encode("utf-8", "ignore") 这里去掉了，但是AutoGPT里有，很奇怪
            [result for result in results]
        )
    else:
        safe_message = results.encode("utf-8", "ignore").decode("utf-8")
    return safe_message


if __name__ == '__main__':
    SearchEngine.run(query='wtf')
