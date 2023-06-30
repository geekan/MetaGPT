#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/16 10:12
@Author  : alexanderwu
@File    : test_azure_gpt_api.py
"""

from metagpt.provider import AzureGPTAPI


def test_azure_gpt_api():
    api = AzureGPTAPI()
    rsp = api.ask('hello')
    assert len(rsp) > 0
