#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/25 16:24
@Author  : alexanderwu
@File    : azure_hello_world.py
"""
from metagpt.logs import logger
from metagpt.provider import AzureGPTAPI


def azure_gpt_api():
    """Currently, Azure only supports synchronous mode."""
    api = AzureGPTAPI()
    logger.info(api.ask('write python hello world.'))
    logger.info(api.completion([{'role': 'user', 'content': 'hello'}]))


if __name__ == '__main__':
    azure_gpt_api()
