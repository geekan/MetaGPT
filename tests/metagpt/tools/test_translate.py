#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/2 17:46
@Author  : alexanderwu
@File    : test_translate.py
"""

import pytest

from metagpt.logs import logger
from metagpt.tools.translator import Translator


@pytest.mark.asyncio
@pytest.mark.usefixtures("llm_api")
async def test_translate(llm_api):
    poetries = [
        ("Let life be beautiful like summer flowers", "花"),
        ("The ancient Chinese poetries are all songs.", "中国"),
    ]
    for i, j in poetries:
        prompt = Translator.translate_prompt(i)
        rsp = await llm_api.aask(prompt)
        logger.info(rsp)
        assert j in rsp
