#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : search_kb.py
"""
import asyncio

from metagpt.actions import Action
from metagpt.const import DATA_PATH
from metagpt.document_store import FaissStore
from metagpt.logs import logger
from metagpt.roles import Sales
from metagpt.schema import Message

""" example.json, e.g.
[
    {
        "source": "Which facial cleanser is good for oily skin?",
        "output": "ABC cleanser is preferred by many with oily skin."
    },
    {
        "source": "Is L'Oreal good to use?",
        "output": "L'Oreal is a popular brand with many positive reviews."
    }
]
"""


async def search():
    store = FaissStore(DATA_PATH / "example.json")
    role = Sales(profile="Sales", store=store)
    role._watch({Action})
    queries = [
        Message("Which facial cleanser is good for oily skin?", cause_by=Action),
        Message("Is L'Oreal good to use?", cause_by=Action),
    ]
    for query in queries:
        logger.info(f"User: {query}")
        result = await role.run(query)
        logger.info(result)


if __name__ == "__main__":
    asyncio.run(search())
