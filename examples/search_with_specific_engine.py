#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""
import asyncio

from metagpt.config2 import Config
from metagpt.roles import Searcher
from metagpt.tools.search_engine import SearchEngine


async def main():
    question = "What are the most interesting human facts?"

    search = Config.default().search
    kwargs = {"api_key": search.api_key, "cse_id": search.cse_id, "proxy": None}
    await Searcher(search_engine=SearchEngine(engine=search.api_type, **kwargs)).run(question)


if __name__ == "__main__":
    asyncio.run(main())
