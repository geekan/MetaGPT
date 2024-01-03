#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/2 17:46
@Author  : alexanderwu
@File    : test_search_engine.py
"""
from __future__ import annotations

from typing import Callable

import pytest

from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.tools import SearchEngineType
from metagpt.tools.search_engine import SearchEngine


class MockSearchEnine:
    async def run(self, query: str, max_results: int = 8, as_string: bool = True) -> str | list[dict[str, str]]:
        rets = [
            {"url": "https://metagpt.com/mock/{i}", "title": query, "snippet": query * i} for i in range(max_results)
        ]
        return "\n".join(rets) if as_string else rets


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("search_engine_type", "run_func", "max_results", "as_string"),
    [
        (SearchEngineType.SERPAPI_GOOGLE, None, 8, True),
        (SearchEngineType.SERPAPI_GOOGLE, None, 4, False),
        (SearchEngineType.DIRECT_GOOGLE, None, 8, True),
        (SearchEngineType.DIRECT_GOOGLE, None, 6, False),
        (SearchEngineType.SERPER_GOOGLE, None, 8, True),
        (SearchEngineType.SERPER_GOOGLE, None, 6, False),
        (SearchEngineType.DUCK_DUCK_GO, None, 8, True),
        (SearchEngineType.DUCK_DUCK_GO, None, 6, False),
        (SearchEngineType.CUSTOM_ENGINE, MockSearchEnine().run, 8, False),
        (SearchEngineType.CUSTOM_ENGINE, MockSearchEnine().run, 6, False),
    ],
)
async def test_search_engine(search_engine_type, run_func: Callable, max_results: int, as_string: bool):
    # Prerequisites
    if search_engine_type is SearchEngineType.SERPAPI_GOOGLE:
        assert CONFIG.SERPAPI_API_KEY and CONFIG.SERPAPI_API_KEY != "YOUR_API_KEY"
    elif search_engine_type is SearchEngineType.DIRECT_GOOGLE:
        assert CONFIG.GOOGLE_API_KEY and CONFIG.GOOGLE_API_KEY != "YOUR_API_KEY"
        assert CONFIG.GOOGLE_CSE_ID and CONFIG.GOOGLE_CSE_ID != "YOUR_CSE_ID"
    elif search_engine_type is SearchEngineType.SERPER_GOOGLE:
        assert CONFIG.SERPER_API_KEY and CONFIG.SERPER_API_KEY != "YOUR_API_KEY"

    search_engine = SearchEngine(search_engine_type, run_func)
    rsp = await search_engine.run("metagpt", max_results, as_string)
    logger.info(rsp)
    if as_string:
        assert isinstance(rsp, str)
    else:
        assert isinstance(rsp, list)
        assert len(rsp) <= max_results


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
