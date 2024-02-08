#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import warnings
from concurrent import futures
from typing import Optional
from urllib.parse import urlparse

import httplib2
from pydantic import BaseModel, ConfigDict, model_validator

try:
    from googleapiclient.discovery import build
except ImportError:
    raise ImportError(
        "To use this module, you should have the `google-api-python-client` Python package installed. "
        "You can install it by running the command: `pip install -e.[search-google]`"
    )


class GoogleAPIWrapper(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    api_key: str
    cse_id: str
    loop: Optional[asyncio.AbstractEventLoop] = None
    executor: Optional[futures.Executor] = None
    proxy: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def validate_google(cls, values: dict) -> dict:
        if "google_api_key" in values:
            values.setdefault("api_key", values["google_api_key"])
            warnings.warn("`google_api_key` is deprecated, use `api_key` instead", DeprecationWarning, stacklevel=2)

        if "api_key" not in values:
            raise ValueError(
                "To use google search engine, make sure you provide the `api_key` when constructing an object. You can obtain "
                "an API key from https://console.cloud.google.com/apis/credentials."
            )

        if "google_cse_id" in values:
            values.setdefault("cse_id", values["google_cse_id"])
            warnings.warn("`google_cse_id` is deprecated, use `cse_id` instead", DeprecationWarning, stacklevel=2)

        if "cse_id" not in values:
            raise ValueError(
                "To use google search engine, make sure you provide the `cse_id` when constructing an object. You can obtain "
                "the cse_id from https://programmablesearchengine.google.com/controlpanel/create."
            )
        return values

    @property
    def google_api_client(self):
        build_kwargs = {"developerKey": self.api_key}
        if self.proxy:
            parse_result = urlparse(self.proxy)
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
            self.executor, self.google_api_client.list(q=query, num=max_results, cx=self.cse_id).execute
        )
        result = await future
        # Extract the search result items from the response
        search_results = result.get("items", [])

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
