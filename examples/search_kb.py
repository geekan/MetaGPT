#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : search_kb.py
"""
import asyncio

from langchain.embeddings import OpenAIEmbeddings

from metagpt.config import CONFIG
from metagpt.const import DATA_PATH
from metagpt.document_store import FaissStore
from metagpt.logs import logger
from metagpt.roles import Sales

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


def get_store():
    embedding = OpenAIEmbeddings(openai_api_key=CONFIG.openai_api_key, openai_api_base=CONFIG.openai_base_url)
    return FaissStore(DATA_PATH / "example.json", embedding=embedding)


async def search():
    role = Sales(profile="Sales", store=get_store())
    queries = ["Which facial cleanser is good for oily skin?", "Is L'Oreal good to use?"]

    for query in queries:
        logger.info(f"User: {query}")
        result = await role.run(query)
        logger.info(result)


if __name__ == "__main__":
    asyncio.run(search())
