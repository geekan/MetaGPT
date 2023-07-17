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
import json
from pydantic import BaseModel, Field

from metagpt.config import Config


class SerperWrapper(BaseModel):
    """Wrapper around SerpAPI.

    To use, you should have the ``google-search-results`` python package installed,
    and the environment variable ``SERPAPI_API_KEY`` set with your API key, or pass
    `serpapi_api_key` as a named parameter to the constructor.
    """

    search_engine: Any  #: :meta private:
    payload: dict = Field(
        default={
            "page": 1,
            "num": 10
        }
    )
    config = Config()
    serper_api_key: Optional[str] = config.serper_api_key
    aiosession: Optional[aiohttp.ClientSession] = None

    class Config:
        arbitrary_types_allowed = True

    async def run(self, query: str, **kwargs: Any) -> str:
        """Run query through Serper and parse result async."""
        return ";".join([self._process_response(res) for res in await self.results(query)])

    async def results(self, queries: list[str]) -> dict:
        """Use aiohttp to run query through Serper and return the results async."""

        def construct_url_and_payload_and_headers() -> Tuple[str, Dict[str, str]]:
            payloads = self.get_payloads(queries)
            url = "https://google.serper.dev/search"
            headers = self.get_headers()
            return url, payloads, headers

        url, payloads, headers = construct_url_and_payload_and_headers()
        if not self.aiosession:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=payloads, headers=headers) as response:
                    res = await response.json()
                    
        else:
            async with self.aiosession.get.post(url, data=payloads, headers=headers) as response:
                res = await response.json()

        return res

    def get_payloads(self, queries: list[str]) -> Dict[str, str]:
        """Get payloads for Serper."""
        payloads = []
        for query in queries:
            _payload = {
                "q": query,
            }
            payloads.append({**self.payload, **_payload})
        return json.dumps(payloads, sort_keys=True)

    def get_headers(self) -> Dict[str, str]:
        headers = {
            'X-API-KEY':  self.serper_api_key,
            'Content-Type': 'application/json'
        }
        return headers

    @staticmethod
    def _process_response(res: dict) -> str:
        """Process response from SerpAPI."""
        # logger.debug(res)
        focus = ['title', 'snippet', 'link']
        def get_focused(x): return {i: j for i, j in x.items() if i in focus}

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
        elif "snippet" in res["organic"][0].keys():
            toret = res["organic"][0]["snippet"]
        else:
            toret = "No good search result found"

        toret_l = []
        if "answer_box" in res.keys() and "snippet" in res["answer_box"].keys():
            toret_l += [get_focused(res["answer_box"])]
        if res.get("organic"):
            toret_l += [get_focused(i) for i in res.get("organic")]

        return str(toret) + '\n' + str(toret_l)
