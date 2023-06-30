#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/23 18:27
@Author  : alexanderwu
@File    : search_engine_serpapi.py
"""
from typing import Any, Dict, Optional, Tuple
from metagpt.logs import logger
import aiohttp
from pydantic import BaseModel, Field

from metagpt.config import Config


class SerpAPIWrapper(BaseModel):
    """Wrapper around SerpAPI.

    To use, you should have the ``google-search-results`` python package installed,
    and the environment variable ``SERPAPI_API_KEY`` set with your API key, or pass
    `serpapi_api_key` as a named parameter to the constructor.
    """

    search_engine: Any  #: :meta private:
    params: dict = Field(
        default={
            "engine": "google",
            "google_domain": "google.com",
            "gl": "us",
            "hl": "en",
        }
    )
    config = Config()
    serpapi_api_key: Optional[str] = config.serpapi_api_key
    aiosession: Optional[aiohttp.ClientSession] = None

    class Config:
        arbitrary_types_allowed = True

    async def run(self, query: str, **kwargs: Any) -> str:
        """Run query through SerpAPI and parse result async."""
        return self._process_response(await self.results(query))

    async def results(self, query: str) -> dict:
        """Use aiohttp to run query through SerpAPI and return the results async."""

        def construct_url_and_params() -> Tuple[str, Dict[str, str]]:
            params = self.get_params(query)
            params["source"] = "python"
            if self.serpapi_api_key:
                params["serp_api_key"] = self.serpapi_api_key
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
    def _process_response(res: dict) -> str:
        """Process response from SerpAPI."""
        # logger.debug(res)
        focus = ['title', 'snippet', 'link']
        get_focused = lambda x: {i: j for i, j in x.items() if i in focus}

        if "error" in res.keys():
            raise ValueError(f"Got error from SerpAPI: {res['error']}")
        if "answer_box" in res.keys() and "answer" in res["answer_box"].keys():
            toret = res["answer_box"]["answer"]
        elif "answer_box" in res.keys() and "snippet" in res["answer_box"].keys():
            toret = res["answer_box"]["snippet"]
        elif (
            "answer_box" in res.keys()
            and "snippet_highlighted_words" in res["answer_box"].keys()
        ):
            toret = res["answer_box"]["snippet_highlighted_words"][0]
        elif (
            "sports_results" in res.keys()
            and "game_spotlight" in res["sports_results"].keys()
        ):
            toret = res["sports_results"]["game_spotlight"]
        elif (
            "knowledge_graph" in res.keys()
            and "description" in res["knowledge_graph"].keys()
        ):
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

        return str(toret) + '\n' + str(toret_l)
