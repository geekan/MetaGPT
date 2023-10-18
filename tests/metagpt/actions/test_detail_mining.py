#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/13 00:26
@Author  : fisherdeng
@File    : test_detail_mining.py
"""
import pytest

from metagpt.actions.detail_mining import DetailMining
from metagpt.logs import logger

@pytest.mark.asyncio
async def test_detail_mining():
    topic = "如何做一个生日蛋糕"
    record = "我认为应该先准备好材料，然后再开始做蛋糕。"
    detail_mining = DetailMining("detail_mining")
    rsp = await detail_mining.run(topic=topic, record=record)
    logger.info(f"{rsp.content=}")
    
    assert '##OUTPUT' in rsp.content
    assert '蛋糕' in rsp.content

