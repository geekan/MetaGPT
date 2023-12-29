#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/30
@Author  : mashenquan
@File    : test_metagpt_llm_api.py
"""
from metagpt.provider.metagpt_api import MetaGPTLLM


def test_metagpt():
    llm = MetaGPTLLM()
    assert llm


if __name__ == "__main__":
    test_metagpt()
