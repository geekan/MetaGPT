#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/5/23 18:27
# @Author  : alexanderwu
# @File    : search_engine_serpapi.py

from typing import Any, Dict, Optional, Tuple

import aiohttp
from pydantic import BaseModel, ConfigDict, Field, field_validator

from metagpt.config2 import config


class SerpAPIWrapper(BaseModel):
    """A wrapper for SerpAPI searches.

    This class provides methods to perform searches using SerpAPI and process the results.

    Attributes:
        model_config: Configuration dictionary allowing arbitrary types.
        search_engine: The search engine to use. Defaults to None.
        params: Default parameters for the search engine.
        serpapi_api_key: The API key for SerpAPI. If not provided, it tries to fetch from config.
        aiosession: An optional aiohttp.ClientSession for making requests.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    search_engine: Any = None  #: :meta private:
    params: dict = Field(
        default_factory=lambda: {
            "engine": "google",
            "google_domain": "google.com",
            "gl": "us",
            "hl": "en",
        }
    )
    # should add `validate_default=True` to check with default value
    serpapi_api_key: Optional[str] = Field(default=None, validate_default=True)
    aiosession: Optional[aiohttp.ClientSession] = None

    @field_validator("serpapi_api_key", mode="before")
    @classmethod
    def check_serpapi_api_key(cls, val: str):
        """Validates the SerpAPI API key.

        Args:
            val: The API key to validate.

        Returns:
            The validated API key.

        Raises:
            ValueError: If the API key is not provided and not found in the environment.
        """
        val = val or config.search.api_key
        if not val:
            raise ValueError(
                "To use, make sure you provide the serpapi_api_key when constructing an object. Alternatively, "
                "ensure that the environment variable SERPAPI_API_KEY is set with your API key. You can obtain "
                "an API key from https://serpapi.com/."
            )
        return val

    async def run(self, query, max_results: int = 8, as_string: bool = True, **kwargs: Any) -> str:
        """Run query through SerpAPI and parse result async."""
        result = await self.results(query, max_results)
        return self._process_response(result, as_string=as_string)

    async def results(self, query: str, max_results: int) -> dict:
        """Use aiohttp to run query through SerpAPI and return the results async."""

        def construct_url_and_params() -> Tuple[str, Dict[str, str]]:
            params = self.get_params(query)
            params["source"] = "python"
            params["num"] = max_results
            params["output"] = "json"
            url = "https://serpapi.com/search"
            return url, params

        url, params = construct_url_and_params()
        if not self.aiosession:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    res = await response.json()
        else:
            async with self.aiosession.get(url, params=params) as response:
                res = await response.json()

        return res

    def get_params(self, query: str) -> Dict[str, str]:
        """Get parameters for SerpAPI."""
        _params = {
            "api_key": self.serpapi_api_key,
            "q": query,
        }
        params = {**self.params, **_params}
        return params

    @staticmethod
    def _process_response(res: dict, as_string: bool) -> str:
        """Process response from SerpAPI."""
        # logger.debug(res)
        focus = ["title", "snippet", "link"]
        get_focused = lambda x: {i: j for i, j in x.items() if i in focus}

        if "error" in res.keys():
            raise ValueError(f"Got error from SerpAPI: {res['error']}")
        if "answer_box" in res.keys() and "answer" in res["answer_box"].keys():
            toret = res["answer_box"]["answer"]
        elif "answer_box" in res.keys() and "snippet" in res["answer_box"].keys():
            toret = res["answer_box"]["snippet"]
        elif "answer_box" in res.keys() and "snippet_highlighted_words" in res["answer_box"].keys():
            toret = res["answer_box"]["snippet_highlighted_words"][0]
        elif "sports_results" in res.keys() and "game_spotlight" in res["sports_results"].keys():
            toret = res["sports_results"]["game_spotlight"]
        elif "knowledge_graph" in res.keys() and "description" in res["knowledge_graph"].keys():
            toret = res["knowledge_graph"]["description"]
        elif "snippet" in res["organic_results"][0].keys():
            toret = res["organic_results"][0]["snippet"]
        else:
            toret = "No good search result found"

        toret_l = []
        if "answer_box" in res.keys() and "snippet" in res["answer_box"].keys():
            toret_l += [get_focused(res["answer_box"])]
        if res.get("organic_results"):
            toret_l += [get_focused(i) for i in res.get("organic_results")]

        return str(toret) + "\n" + str(toret_l) if as_string else toret_l


if __name__ == "__main__":
    import fire

    fire.Fire(SerpAPIWrapper().run)
