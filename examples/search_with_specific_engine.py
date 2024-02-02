#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""
import asyncio

from metagpt.roles import Searcher
from metagpt.tools.search_engine import SearchEngine, SearchEngineType


async def main():
    question = "What are the most interesting human facts?"
    kwargs = {"api_key": "", "cse_id": "", "proxy": None}
    # Serper API
    # await Searcher(search_engine=SearchEngine(engine=SearchEngineType.SERPER_GOOGLE, **kwargs)).run(question)
    # SerpAPI
    # await Searcher(search_engine=SearchEngine(engine=SearchEngineType.SERPAPI_GOOGLE, **kwargs)).run(question)
    # Google API
    # await Searcher(search_engine=SearchEngine(engine=SearchEngineType.DIRECT_GOOGLE, **kwargs)).run(question)
    # DDG API
    await Searcher(search_engine=SearchEngine(engine=SearchEngineType.DUCK_DUCK_GO, **kwargs)).run(question)


if __name__ == "__main__":
    asyncio.run(main())
