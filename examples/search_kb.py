#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : search_kb.py
@Modified By: mashenquan, 2023-12-22. Delete useless codes.
"""
import asyncio

from langchain.embeddings import OpenAIEmbeddings

from metagpt.config2 import config
from metagpt.const import DATA_PATH, EXAMPLE_PATH
from metagpt.document_store import FaissStore
from metagpt.logs import logger
from metagpt.roles import Sales


def get_store():
    llm = config.get_openai_llm()
    embedding = OpenAIEmbeddings(openai_api_key=llm.api_key, openai_api_base=llm.base_url)
    return FaissStore(DATA_PATH / "example.json", embedding=embedding)


async def search():
    store = FaissStore(EXAMPLE_PATH / "example.json")
    role = Sales(profile="Sales", store=store)
    query = "Which facial cleanser is good for oily skin?"
    result = await role.run(query)
    logger.info(result)


if __name__ == "__main__":
    asyncio.run(search())
