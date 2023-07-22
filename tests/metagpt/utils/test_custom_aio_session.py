#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/7 17:23
@Author  : alexanderwu
@File    : test_custom_aio_session.py
"""
from metagpt.logs import logger
from metagpt.provider.openai_api import OpenAIGPTAPI


async def try_hello(api):
    batch = [[{'role': 'user', 'content': 'hello'}]]
    results = await api.acompletion_batch_text(batch)
    return results


async def aask_batch(api: OpenAIGPTAPI):
    results = await api.aask_batch(['hi', 'write python hello world.'])
    logger.info(results)
    return results
