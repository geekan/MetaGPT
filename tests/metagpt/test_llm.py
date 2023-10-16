#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:45
@Author  : alexanderwu
@File    : test_llm.py
"""

import pytest

from metagpt.llm import LLM


@pytest.fixture()
def llm():
    return LLM()


@pytest.mark.asyncio
async def test_llm_aask(llm):
    assert len(await llm.aask('hello world')) > 0


@pytest.mark.asyncio
async def test_llm_aask_batch(llm):
    assert len(await llm.aask_batch(['hi', 'write python hello world.'])) > 0


@pytest.mark.asyncio
async def test_llm_acompletion(llm):
    hello_msg = [{'role': 'user', 'content': 'hello'}]
    assert len(await llm.acompletion(hello_msg)) > 0
    assert len(await llm.acompletion_batch([hello_msg])) > 0
    assert len(await llm.acompletion_batch_text([hello_msg])) > 0
