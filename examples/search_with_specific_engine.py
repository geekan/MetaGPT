#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""
import asyncio

from metagpt.roles import Searcher
from metagpt.tools import SearchEngineType


async def main():
    question = "What are the most interesting human facts?"
    # Serper API
    # await Searcher(engine=SearchEngineType.SERPER_GOOGLE).run(question)
    # SerpAPI
    await Searcher(engine=SearchEngineType.SERPAPI_GOOGLE).run(question)
    # Google API
    # await Searcher(engine=SearchEngineType.DIRECT_GOOGLE).run(question)


if __name__ == "__main__":
    asyncio.run(main())
