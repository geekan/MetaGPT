#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : search_kb.py
"""
import asyncio

from metagpt.const import DATA_PATH
from metagpt.document_store import FaissStore
from metagpt.logs import logger
from metagpt.roles import Sales


async def search():
    store = FaissStore(DATA_PATH / 'example.json')
    role = Sales(profile="Sales", store=store)

    queries = ["Which facial cleanser is good for oily skin?", "Is L'Oreal good to use?"]
    for query in queries:
        logger.info(f"User: {query}")
        result = await role.run(query)
        logger.info(result)


if __name__ == '__main__':
    asyncio.run(search())
