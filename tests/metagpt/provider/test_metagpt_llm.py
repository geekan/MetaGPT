#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/30
@Author  : mashenquan
@File    : test_metagpt_llm.py
"""
from metagpt.provider.metagpt_api import MetaGPTLLM
from tests.metagpt.provider.mock_llm_config import mock_llm_config


def test_metagpt():
    llm = MetaGPTLLM(mock_llm_config)
    assert llm


if __name__ == "__main__":
    test_metagpt()
