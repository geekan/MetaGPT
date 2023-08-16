#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
from concurrent import futures
from urllib.parse import urlparse

import httplib2
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from metagpt.config import CONFIG
from metagpt.logs import logger


class GoogleAPIWrapper:
    """Wrapper around GoogleAPI.

    To use this module, you should have the `google-api-python-client` Python package installed
    and set property values for the configurations `GOOGLE_API_KEY` and `GOOGLE_CSE_ID`. See 
    https://programmablesearchengine.google.com/controlpanel/all.
    """
    def __init__(
        self,
        *,
        loop: asyncio.AbstractEventLoop | None = None,
        executor: futures.Executor | None = None,
    ):
        build_kwargs = {"developerKey": CONFIG.google_api_key}
        if CONFIG.global_proxy:
            parse_result = urlparse(CONFIG.global_proxy)
            proxy_type = parse_result.scheme
            if proxy_type == "https":
                proxy_type = "http"
            build_kwargs["http"] = httplib2.Http(
                proxy_info=httplib2.ProxyInfo(
                    getattr(httplib2.socks, f"PROXY_TYPE_{proxy_type.upper()}"),
                    parse_result.hostname,
                    parse_result.port,
                ),
            )
        service = build("customsearch", "v1", **build_kwargs)
        self.google_api_client = service.cse()
        self.custom_search_engine_id = CONFIG.google_cse_id
        self.loop = loop
        self.executor = executor

    async def run(
        self,
        query: str,
        max_results: int = 8,
        as_string: bool = True,
        focus: list[str] | None = None,
    ) -> str | list[dict]:
        """Return the results of a Google search using the official Google API.

        Args:
            query: The search query.
            max_results: The number of results to return.
            as_string: A boolean flag to determine the return type of the results. If True, the function will
                return a formatted string with the search results. If False, it will return a list of dictionaries
                containing detailed information about each search result.
            focus: Specific information to be focused on from each search result.

        Returns:
            The results of the search.
        """
        loop = self.loop or asyncio.get_event_loop()
        future = loop.run_in_executor(
            self.executor,
            self.google_api_client.list(
                q=query,
                num=max_results,
                cx=self.custom_search_engine_id
            ).execute
        )
        try:
            result = await future
            # Extract the search result items from the response
            search_results = result.get("items", [])

        except HttpError as e:
            # Handle errors in the API call
            logger.exception(f"fail to search {query} for {e}")
            search_results = []
        
        focus = focus or ["snippet", "link", "title"]
        details = [{i: j for i, j in item_dict.items() if i in focus} for item_dict in search_results]
        # Return the list of search result URLs
        if as_string:
            return safe_google_results(details)
        
        return details


def safe_google_results(results: str | list) -> str:
    """Return the results of a google search in a safe format.

    Args:
        results: The search results.

    Returns:
        The results of the search.
    """
    if isinstance(results, list):
        safe_message = json.dumps([result for result in results])
    else:
        safe_message = results.encode("utf-8", "ignore").decode("utf-8")
    return safe_message


if __name__ == "__main__":
    import fire

    fire.Fire(GoogleAPIWrapper().run)
