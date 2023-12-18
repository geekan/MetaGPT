#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/18 19:08
@Author  : zhongyang
@File    : test_openai_api.py
"""

import pytest

from metagpt.llm import LLM
from metagpt.logs import logger


@pytest.mark.asyncio
async def test_update_rpm():
    llm = LLM()

    await llm.update_rpm()
    assert isinstance(llm.rpm, int)
