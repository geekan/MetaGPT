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
    rsp = await llm.aask("hello world", stream=False)
    assert len(rsp) > 0


@pytest.mark.asyncio
async def test_llm_aask_stream(llm):
    rsp = await llm.aask("hello world", stream=True)
    assert len(rsp) > 0


@pytest.mark.asyncio
async def test_llm_acompletion(llm):
    hello_msg = [{"role": "user", "content": "hello"}]
    rsp = await llm.acompletion(hello_msg)
    assert len(rsp.choices[0].message.content) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
