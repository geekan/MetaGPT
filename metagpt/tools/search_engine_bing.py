#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import warnings
from typing import Optional

import aiohttp
from pydantic import BaseModel, ConfigDict, model_validator


class BingAPIWrapper(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    api_key: str
    bing_url: str = "https://api.bing.microsoft.com/v7.0/search"
    aiosession: Optional[aiohttp.ClientSession] = None
    proxy: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def validate_api_key(cls, values: dict) -> dict:
        if "api_key" in values:
            values.setdefault("api_key", values["api_key"])
            warnings.warn("`api_key` is deprecated, use `api_key` instead", DeprecationWarning, stacklevel=2)
        return values

    @property
    def header(self):
        return {"Ocp-Apim-Subscription-Key": self.api_key}

    async def run(
        self,
        query: str,
        max_results: int = 8,
        as_string: bool = True,
        focus: list[str] | None = None,
    ) -> str | list[dict]:
        """Return the results of a Google search using the official Bing API.

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
        params = {
            "q": query,
            "count": max_results,
            "textFormat": "HTML",
        }
        result = await self.results(params)
        search_results = result["webPages"]["value"]
        focus = focus or ["snippet", "link", "title"]
        for item_dict in search_results:
            item_dict["link"] = item_dict["url"]
            item_dict["title"] = item_dict["name"]
        details = [{i: j for i, j in item_dict.items() if i in focus} for item_dict in search_results]
        if as_string:
            return safe_results(details)
        return details

    async def results(self, params: dict) -> dict:
        """Use aiohttp to run query and return the results async."""

        if not self.aiosession:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.bing_url, params=params, headers=self.header, proxy=self.proxy) as response:
                    response.raise_for_status()
                    res = await response.json()
        else:
            async with self.aiosession.get(
                self.bing_url, params=params, headers=self.header, proxy=self.proxy
            ) as response:
                response.raise_for_status()
                res = await response.json()

        return res


def safe_results(results: str | list) -> str:
    """Return the results of a bing search in a safe format.

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

    fire.Fire(BingAPIWrapper().run)
