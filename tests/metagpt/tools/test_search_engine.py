#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/2 17:46
@Author  : alexanderwu
@File    : test_search_engine.py
"""

import pytest
from metagpt.logs import logger
from metagpt.tools.search_engine import SearchEngine


@pytest.mark.asyncio
@pytest.mark.usefixtures("llm_api")
async def test_search_engine(llm_api):
    search_engine = SearchEngine()
    poetries = [
        # ("北京美食", "北京"),
        ("屈臣氏", "屈臣氏")
    ]
    for i, j in poetries:
        rsp = await search_engine.run(i)
        # rsp = context.llm.ask_batch([prompt])
        logger.info(rsp)
        # assert any(j in k['body'] for k in rsp)
        assert len(rsp) > 0
