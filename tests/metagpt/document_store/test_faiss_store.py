#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/27 20:20
@Author  : alexanderwu
@File    : test_faiss_store.py
"""

import pytest

from metagpt.const import EXAMPLE_PATH
from metagpt.document_store import FaissStore
from metagpt.logs import logger
from metagpt.roles import Sales


@pytest.mark.asyncio
async def test_search_json():
    store = FaissStore(EXAMPLE_PATH / "example.json")
    role = Sales(profile="Sales", store=store)
    query = "Which facial cleanser is good for oily skin?"
    result = await role.run(query)
    logger.info(result)


@pytest.mark.asyncio
async def test_search_xlsx():
    store = FaissStore(EXAMPLE_PATH / "example.xlsx")
    role = Sales(profile="Sales", store=store)
    query = "Which facial cleanser is good for oily skin?"
    result = await role.run(query)
    logger.info(result)


@pytest.mark.asyncio
async def test_write():
    store = FaissStore(EXAMPLE_PATH / "example.xlsx", meta_col="Answer", content_col="Question")
    _faiss_store = store.write()
    assert _faiss_store.docstore
    assert _faiss_store.index
