#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
from concurrent import futures
from typing import Optional
from urllib.parse import urlparse

import httplib2
from pydantic import BaseModel, ConfigDict, Field, field_validator

from metagpt.config2 import config
from metagpt.logs import logger

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    raise ImportError(
        "To use this module, you should have the `google-api-python-client` Python package installed. "
        "You can install it by running the command: `pip install -e.[search-google]`"
    )


class GoogleAPIWrapper(BaseModel):
    """A wrapper class for Google API interactions.

    This class provides a simplified interface to interact with Google's Custom Search Engine API.
    It allows for executing search queries and processing the results.

    Attributes:
        model_config: Configuration for the Pydantic model allowing arbitrary types.
        google_api_key: Optional API key for accessing Google's API. If not provided, it attempts to use a default from the configuration.
        google_cse_id: Optional Custom Search Engine ID. If not provided, it attempts to use a default from the configuration.
        loop: Optional event loop. If not provided, the default asyncio event loop is used.
        executor: Optional executor for running blocking tasks. If not provided, the default executor is used.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    google_api_key: Optional[str] = Field(default=None, validate_default=True)
    google_cse_id: Optional[str] = Field(default=None, validate_default=True)
    loop: Optional[asyncio.AbstractEventLoop] = None
    executor: Optional[futures.Executor] = None

    @field_validator("google_api_key", mode="before")
    @classmethod
    def check_google_api_key(cls, val: str):
        """Validates and possibly retrieves the Google API key.

        This method checks if the provided API key is valid. If not provided, it attempts to retrieve the key from the configuration.

        Args:
            val: The provided Google API key.

        Returns:
            The validated or retrieved Google API key.

        Raises:
            ValueError: If no valid Google API key is provided or found in the configuration.
        """
        val = val or config.search.api_key
        if not val:
            raise ValueError(
                "To use, make sure you provide the google_api_key when constructing an object. Alternatively, "
                "ensure that the environment variable GOOGLE_API_KEY is set with your API key. You can obtain "
                "an API key from https://console.cloud.google.com/apis/credentials."
            )
        return val

    @field_validator("google_cse_id", mode="before")
    @classmethod
    def check_google_cse_id(cls, val: str):
        """Validates and possibly retrieves the Google Custom Search Engine ID.

        This method checks if the provided CSE ID is valid. If not provided, it attempts to retrieve the ID from the configuration.

        Args:
            val: The provided Google Custom Search Engine ID.

        Returns:
            The validated or retrieved Google Custom Search Engine ID.

        Raises:
            ValueError: If no valid Google CSE ID is provided or found in the configuration.
        """
        val = val or config.search.cse_id
        if not val:
            raise ValueError(
                "To use, make sure you provide the google_cse_id when constructing an object. Alternatively, "
                "ensure that the environment variable GOOGLE_CSE_ID is set with your API key. You can obtain "
                "an API key from https://programmablesearchengine.google.com/controlpanel/create."
            )
        return val

    @property
    def google_api_client(self):
        """Creates and returns a Google API client for the Custom Search Engine.

        This property checks for proxy settings in the configuration and applies them if present.

        Returns:
            A Google API client for the Custom Search Engine.
        """
        build_kwargs = {"developerKey": self.google_api_key}
        if config.proxy:
            parse_result = urlparse(config.proxy)
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
        return service.cse()

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
            self.executor, self.google_api_client.list(q=query, num=max_results, cx=self.google_cse_id).execute
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
