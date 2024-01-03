#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:45
@Author  : alexanderwu
@File    : test_llm.py
@Modified By: mashenquan, 2023/8/20. Remove global configuration `CONFIG`, enable configuration support for business isolation.
"""

import pytest

from metagpt.provider.openai_api import OpenAILLM as LLM


@pytest.fixture()
def llm():
    return LLM()


@pytest.mark.asyncio
async def test_llm_aask(llm):
    rsp = await llm.aask("hello world", stream=False)
    assert len(rsp) > 0


@pytest.mark.asyncio
async def test_llm_acompletion(llm):
    hello_msg = [{"role": "user", "content": "hello"}]
    rsp = await llm.acompletion(hello_msg)
    assert len(rsp.choices[0].message.content) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
