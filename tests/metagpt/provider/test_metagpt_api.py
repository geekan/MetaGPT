#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/28
@Author  : mashenquan
@File    : test_metagpt_api.py
"""
from metagpt.config import LLMProviderEnum
from metagpt.llm import LLM


def test_llm():
    llm = LLM(provider=LLMProviderEnum.METAGPT)
    assert llm
