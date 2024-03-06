#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""
import asyncio

from metagpt.roles import Searcher
from metagpt.tools.search_engine import SearchEngine, SearchEngineType
from metagpt.config2 import Config


async def main():
    question = "What are the most interesting human facts?"

    search = Config.default().search
    kwargs = {"api_key": search.api_key, "cse_id": search.cse_id, "proxy": None}

    if search.api_type == SearchEngineType.DIRECT_GOOGLE:
        # Google API
        await Searcher(
            search_engine=SearchEngine(engine=SearchEngineType.DIRECT_GOOGLE, **kwargs)
        ).run(question)
    elif search.api_type == SearchEngineType.SERPER_GOOGLE:
        # Serper API
        await Searcher(
            search_engine=SearchEngine(engine=SearchEngineType.SERPER_GOOGLE, **kwargs)
        ).run(question)
    elif search.api_type == SearchEngineType.SERPAPI_GOOGLE:
        # SerpAPI
        await Searcher(
            search_engine=SearchEngine(engine=SearchEngineType.SERPAPI_GOOGLE, **kwargs)
        ).run(question)
    else:
        # DDG API
        await Searcher(
            search_engine=SearchEngine(engine=SearchEngineType.DUCK_DUCK_GO, **kwargs)
        ).run(question)


if __name__ == "__main__":
    asyncio.run(main())
