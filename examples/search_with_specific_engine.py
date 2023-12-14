#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Modified By: mashenquan, 2023-8-9, fix-bug: cannot find metagpt module.
"""
import asyncio
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from metagpt.roles import Searcher
from metagpt.tools import SearchEngineType


async def main():
    # Serper API
    # await Searcher(engine = SearchEngineType.SERPER_GOOGLE).run(["What are some good sun protection products?","What are some of the best beaches?"])
    # SerpAPI
    # await Searcher(engine=SearchEngineType.SERPAPI_GOOGLE).run("What are the best ski brands for skiers?")
    # Google API
    await Searcher(engine=SearchEngineType.DIRECT_GOOGLE).run("What are the most interesting human facts?")


if __name__ == "__main__":
    asyncio.run(main())
