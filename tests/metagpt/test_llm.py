#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:45
@Author  : alexanderwu
@File    : test_llm.py
@Modified By: mashenquan, 2023/8/20. Remove global configuration `CONFIG`, enable configuration support for business isolation.
"""

import pytest

from metagpt.config import Config
from metagpt.provider.openai_api import OpenAIGPTAPI as LLM, CostManager


@pytest.fixture()
def llm():
    options = Config().runtime_options
    return LLM(options=options, cost_manager=CostManager(**options))


@pytest.mark.asyncio
async def test_llm_aask(llm):
    assert len(await llm.aask("hello world")) > 0


@pytest.mark.asyncio
async def test_llm_aask_batch(llm):
    assert len(await llm.aask_batch(["hi", "write python hello world."])) > 0


@pytest.mark.asyncio
async def test_llm_acompletion(llm):
    hello_msg = [{"role": "user", "content": "hello"}]
    assert len(await llm.acompletion(hello_msg)) > 0
    assert len(await llm.acompletion_batch([hello_msg])) > 0
    assert len(await llm.acompletion_batch_text([hello_msg])) > 0

# if __name__ == "__main__":
#     pytest.main([__file__, "-s"])
