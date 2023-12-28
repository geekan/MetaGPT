#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/28
@Author  : mashenquan
@File    : test_open_llm_api.py
"""
from metagpt.config import CONFIG, LLMProviderEnum
from metagpt.llm import LLM
from metagpt.provider.open_llm_api import OpenLLMCostManager


def test_llm():
    llm = LLM(provider=LLMProviderEnum.OPEN_LLM)
    assert llm


def test_cost():
    # Prerequisites
    CONFIG.max_budget = 10

    cost = OpenLLMCostManager()
    cost.update_cost(prompt_tokens=10, completion_tokens=1, model="gpt-35-turbo")
    assert cost.get_total_prompt_tokens() > 0
    assert cost.get_total_completion_tokens() > 0
