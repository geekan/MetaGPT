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

from metagpt.configs.search_config import SearchConfig
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
        (SearchEngineType.BING, None, 6, False),
        (SearchEngineType.CUSTOM_ENGINE, MockSearchEnine().run, 8, False),
        (SearchEngineType.CUSTOM_ENGINE, MockSearchEnine().run, 6, False),
    ],
)
async def test_search_engine(
    search_engine_type,
    run_func: Callable,
    max_results: int,
    as_string: bool,
    search_engine_mocker,
):
    # Prerequisites
    search_engine_config = {"engine": search_engine_type, "run_func": run_func}

    if search_engine_type is SearchEngineType.SERPAPI_GOOGLE:
        search_engine_config["api_key"] = "mock-serpapi-key"
    elif search_engine_type is SearchEngineType.DIRECT_GOOGLE:
        search_engine_config["api_key"] = "mock-google-key"
        search_engine_config["cse_id"] = "mock-google-cse"
    elif search_engine_type is SearchEngineType.SERPER_GOOGLE:
        search_engine_config["api_key"] = "mock-serper-key"

    async def test(search_engine):
        rsp = await search_engine.run("metagpt", max_results, as_string)
        logger.info(rsp)
        if as_string:
            assert isinstance(rsp, str)
        else:
            assert isinstance(rsp, list)
            assert len(rsp) <= max_results

    await test(SearchEngine(**search_engine_config))
    search_engine_config["api_type"] = search_engine_config.pop("engine")
    if run_func:
        await test(SearchEngine.from_search_func(run_func))
        search_engine_config["search_func"] = search_engine_config.pop("run_func")
    await test(SearchEngine.from_search_config(SearchConfig(**search_engine_config)))


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
