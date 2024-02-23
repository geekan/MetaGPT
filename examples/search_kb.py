#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : search_kb.py
@Modified By: mashenquan, 2023-12-22. Delete useless codes.
"""
import asyncio

from metagpt.const import EXAMPLE_DATA_PATH
from metagpt.document_store import FaissStore
from metagpt.logs import logger
from metagpt.roles import Sales


async def search():
    store = FaissStore(EXAMPLE_DATA_PATH / "search_kb/example.json")
    role = Sales(profile="Sales", store=store)
    query = "Which facial cleanser is good for oily skin?"
    result = await role.run(query)
    logger.info(result)


if __name__ == "__main__":
    asyncio.run(search())
