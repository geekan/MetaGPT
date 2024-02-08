#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/18 19:08
@Author  : zhongyang
@File    : test_openai_api.py
"""

import pytest

from metagpt.logs import logger
from metagpt.provider.openai_api import OpenAILLM
from metagpt.config2 import config

@pytest.mark.asyncio
async def test_update_rpm():
    llm = OpenAILLM(config)
    await llm.update_rpm()
    assert isinstance(llm.rpm, float)