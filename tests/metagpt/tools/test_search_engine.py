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
from metagpt.tools.search_engine_bing import BingAPIWrapper


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
    mocker,
):
    mocker.patch.object(
        BingAPIWrapper,
        "results",
        return_value={
            "webPages": {
                "value": [
                    {
                        "url": "https://github.com/geekan/MetaGPT",
                        "snippet": "geekan/MetaGPT. This commit does not belong to any branch on this repository, and may belong to a fork outside of the repository. About. 🌟 The Multi-Agent Framework: Given one line Requirement, return PRD, Design, Tasks, Repo deepwisdom.ai/ Topics. agent multi-agent gpt hacktoberfest llm metagpt Resources. Readme",
                        "name": "MetaGPT: The Multi-Agent Framework - GitHub",
                    },
                    {
                        "url": "https://docs.deepwisdom.ai/",
                        "snippet": "MetaGPT. The Multi-Agent Framework. Assign different roles to GPTs to form a collaborative software entity for complex tasks. Get Started. View on Github. Agents. Explore agent creation, configuration, and management, including algorithms and techniques. Demos.",
                        "name": "MetaGPT | MetaGPT",
                    },
                    {
                        "url": "https://www.unite.ai/metagpt-complete-guide-to-the-best-ai-agent-available-right-now/",
                        "snippet": "MetaGPT is a Multi-agent system that utilizes Large Language models and Standardized Operating Procedures to generate code in real-time. It outperforms other AI agents in code generation, collaboration, and code review. Learn how to install and use MetaGPT with examples and benchmarks.",
                        "name": "MetaGPT: Complete Guide to the Best AI Agent Available Right Now",
                    },
                    {
                        "url": "https://docs.deepwisdom.ai/main/en/guide/get_started/introduction.html",
                        "snippet": "Internally, MetaGPT includes product managers / architects / project managers / engineers. It provides the entire process of a software company along with carefully orchestrated SOPs. Code = SOP (Team) is the core philosophy. We materialize SOP and apply it to teams composed of LLMs. Software Company Multi-Role Schematic.",
                        "name": "MetaGPT: The Multi-Agent Framework | MetaGPT",
                    },
                    {
                        "url": "https://arxiv.org/abs/2308.00352",
                        "snippet": "MetaGPT is a novel method that uses human workflows to improve the performance of LLM-based multi-agent systems. It encodes SOPs into prompt sequences and assigns roles to agents to break down complex tasks into subtasks.",
                        "name": "MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework",
                    },
                    {
                        "url": "https://github.com/geekan/MetaGPT/blob/main/README.md",
                        "snippet": "MetaGPT takes a one line requirement as input and outputs user stories / competitive analysis / requirements / data structures / APIs / documents, etc. \\n Internally, MetaGPT includes product managers / architects / project managers / engineers.",
                        "name": "MetaGPT: The Multi-Agent Framework - GitHub",
                    },
                ]
            }
        },
    )

    # Prerequisites
    search_engine_config = {"engine": search_engine_type, "run_func": run_func}

    if search_engine_type is SearchEngineType.SERPAPI_GOOGLE:
        search_engine_config["api_key"] = "mock-serpapi-key"
    elif search_engine_type is SearchEngineType.DIRECT_GOOGLE:
        search_engine_config["api_key"] = "mock-google-key"
        search_engine_config["cse_id"] = "mock-google-cse"
    elif search_engine_type is SearchEngineType.SERPER_GOOGLE:
        search_engine_config["api_key"] = "mock-serper-key"
    elif search_engine_type is SearchEngineType.BING:
        search_engine_config["api_key"] = "mock-bing-key"

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
