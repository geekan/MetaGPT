#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/28
@Author  : mashenquan
@File    : test_research.py
"""

import pytest

from metagpt.actions import research
from metagpt.tools import SearchEngineType
from metagpt.tools.search_engine import SearchEngine


@pytest.mark.asyncio
async def test_collect_links(mocker, search_engine_mocker, context):
    async def mock_llm_ask(self, prompt: str, system_msgs):
        if "Please provide up to 2 necessary keywords" in prompt:
            return '["metagpt", "llm"]'

        elif "Provide up to 4 queries related to your research topic" in prompt:
            return (
                '["MetaGPT use cases", "The roadmap of MetaGPT", '
                '"The function of MetaGPT", "What llm MetaGPT support"]'
            )
        elif "sort the remaining search results" in prompt:
            return "[1,2]"

    mocker.patch("metagpt.provider.base_llm.BaseLLM.aask", mock_llm_ask)
    resp = await research.CollectLinks(
        search_engine=SearchEngine(engine=SearchEngineType.DUCK_DUCK_GO), context=context
    ).run("The application of MetaGPT")
    for i in ["MetaGPT use cases", "The roadmap of MetaGPT", "The function of MetaGPT", "What llm MetaGPT support"]:
        assert i in resp


@pytest.mark.asyncio
async def test_collect_links_with_rank_func(mocker, search_engine_mocker, context):
    rank_before = []
    rank_after = []
    url_per_query = 4

    def rank_func(results):
        results = results[:url_per_query]
        rank_before.append(results)
        results = results[::-1]
        rank_after.append(results)
        return results

    mocker.patch("metagpt.provider.base_llm.BaseLLM.aask", mock_collect_links_llm_ask)
    resp = await research.CollectLinks(
        search_engine=SearchEngine(engine=SearchEngineType.DUCK_DUCK_GO),
        rank_func=rank_func,
        context=context,
    ).run("The application of MetaGPT")
    for x, y, z in zip(rank_before, rank_after, resp.values()):
        assert x[::-1] == y
        assert [i["link"] for i in y] == z


@pytest.mark.asyncio
async def test_web_browse_and_summarize(mocker, context):
    async def mock_llm_ask(*args, **kwargs):
        return "metagpt"

    mocker.patch("metagpt.provider.base_llm.BaseLLM.aask", mock_llm_ask)
    url = "https://github.com/geekan/MetaGPT"
    url2 = "https://github.com/trending"
    query = "What's new in metagpt"
    resp = await research.WebBrowseAndSummarize(context=context).run(url, query=query)

    assert len(resp) == 1
    assert url in resp
    assert resp[url] == "metagpt"

    resp = await research.WebBrowseAndSummarize(context=context).run(url, url2, query=query)
    assert len(resp) == 2

    async def mock_llm_ask(*args, **kwargs):
        return "Not relevant."

    mocker.patch("metagpt.provider.base_llm.BaseLLM.aask", mock_llm_ask)
    resp = await research.WebBrowseAndSummarize(context=context).run(url, query=query)

    assert len(resp) == 1
    assert url in resp
    assert resp[url] is None


@pytest.mark.asyncio
async def test_conduct_research(mocker, context):
    data = None

    async def mock_llm_ask(*args, **kwargs):
        nonlocal data
        data = f"# Research Report\n## Introduction\n{args} {kwargs}"
        return data

    mocker.patch("metagpt.provider.base_llm.BaseLLM.aask", mock_llm_ask)
    content = (
        "MetaGPT takes a one line requirement as input and "
        "outputs user stories / competitive analysis / requirements / data structures / APIs / documents, etc."
    )

    resp = await research.ConductResearch(context=context).run("The application of MetaGPT", content)
    assert resp == data


async def mock_collect_links_llm_ask(self, prompt: str, system_msgs):
    if "Please provide up to 2 necessary keywords" in prompt:
        return '["metagpt", "llm"]'

    elif "Provide up to 4 queries related to your research topic" in prompt:
        return (
            '["MetaGPT use cases", "The roadmap of MetaGPT", ' '"The function of MetaGPT", "What llm MetaGPT support"]'
        )
    elif "sort the remaining search results" in prompt:
        return "[1,2]"

    return ""


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
