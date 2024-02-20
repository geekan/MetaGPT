#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/5/23 18:27
# @Author  : alexanderwu
# @File    : search_engine_serpapi.py

import json
import warnings
from typing import Any, Dict, Optional, Tuple

import aiohttp
from pydantic import BaseModel, ConfigDict, Field, model_validator


class SerperWrapper(BaseModel):
    """A wrapper for interacting with the Serper API.

    Attributes:
        model_config: Configuration for the model, allowing arbitrary types.
        search_engine: The search engine to be used. Can be any type.
        payload: The default payload for the search query.
        serper_api_key: An optional API key for Serper.
        aiosession: An optional aiohttp.ClientSession for making requests.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    api_key: str
    payload: dict = Field(default_factory=lambda: {"page": 1, "num": 10})
    aiosession: Optional[aiohttp.ClientSession] = None
    proxy: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def validate_serper(cls, values: dict) -> dict:
        if "serper_api_key" in values:
            values.setdefault("api_key", values["serper_api_key"])
            warnings.warn("`serper_api_key` is deprecated, use `api_key` instead", DeprecationWarning, stacklevel=2)

        if "api_key" not in values:
            raise ValueError(
                "To use serper search engine, make sure you provide the `api_key` when constructing an object. You can obtain "
                "an API key from https://serper.dev/."
            )
        return values

    async def run(self, query: str, max_results: int = 8, as_string: bool = True, **kwargs: Any) -> str:
        """Run query through Serper and parse result async.

        Args:
            query: The search query.
            max_results: Maximum number of results to return.
            as_string: Whether to return the result as a string.
            **kwargs: Additional keyword arguments.

        Returns:
            The search results as a string or a list, based on `as_string`.
        """
        if isinstance(query, str):
            return self._process_response((await self.results([query], max_results))[0], as_string=as_string)
        else:
            results = [self._process_response(res, as_string) for res in await self.results(query, max_results)]
        return "\n".join(results) if as_string else results

    async def results(self, queries: list[str], max_results: int = 8) -> dict:
        """Use aiohttp to run query through Serper and return the results async.

        Args:
            queries: A list of search queries.
            max_results: Maximum number of results to return for each query.

        Returns:
            The search results.
        """

        def construct_url_and_payload_and_headers() -> Tuple[str, Dict[str, str]]:
            payloads = self.get_payloads(queries, max_results)
            url = "https://google.serper.dev/search"
            headers = self.get_headers()
            return url, payloads, headers

        url, payloads, headers = construct_url_and_payload_and_headers()
        if not self.aiosession:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=payloads, headers=headers, proxy=self.proxy) as response:
                    response.raise_for_status()
                    res = await response.json()
        else:
            async with self.aiosession.get.post(url, data=payloads, headers=headers, proxy=self.proxy) as response:
                response.raise_for_status()
                res = await response.json()

        return res

    def get_payloads(self, queries: list[str], max_results: int) -> Dict[str, str]:
        """Get payloads for Serper.

        Args:
            queries: A list of search queries.
            max_results: Maximum number of results to return for each query.

        Returns:
            A dictionary of payloads for the queries.
        """
        payloads = []
        for query in queries:
            _payload = {
                "q": query,
                "num": max_results,
            }
            payloads.append({**self.payload, **_payload})
        return json.dumps(payloads, sort_keys=True)

    def get_headers(self) -> Dict[str, str]:
        """Get headers for Serper request.

        Returns:
            A dictionary of headers.
        """
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        return headers

    @staticmethod
    def _process_response(res: dict, as_string: bool = False) -> str:
        """Process response from SerpAPI.

        Args:
            res: The response from SerpAPI.
            as_string: Whether to return the result as a string.

        Returns:
            The processed response as a string or a list, based on `as_string`.

        Raises:
            ValueError: If an error is returned from SerpAPI.
        """
        # logger.debug(res)
        focus = ["title", "snippet", "link"]

        def get_focused(x):
            return {i: j for i, j in x.items() if i in focus}

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
        elif "snippet" in res["organic"][0].keys():
            toret = res["organic"][0]["snippet"]
        else:
            toret = "No good search result found"

        toret_l = []
        if "answer_box" in res.keys() and "snippet" in res["answer_box"].keys():
            toret_l += [get_focused(res["answer_box"])]
        if res.get("organic"):
            toret_l += [get_focused(i) for i in res.get("organic")]

        return str(toret) + "\n" + str(toret_l) if as_string else toret_l


if __name__ == "__main__":
    import fire

    fire.Fire(SerperWrapper().run)
