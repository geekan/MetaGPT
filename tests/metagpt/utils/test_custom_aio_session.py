#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/7 17:23
@Author  : alexanderwu
@File    : test_custom_aio_session.py
"""

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
from metagpt.logs import logger
from metagpt.provider.openai_api import OpenAIGPTAPI
from metagpt.utils.custom_aio_session import CustomAioSession


async def try_hello(api):
    batch = [[{'role': 'user', 'content': 'hello'}],]
    results = await api.acompletion_batch_text(batch)
    return results


async def aask_batch(api: OpenAIGPTAPI):
    results = await api.aask_batch(['hi', 'write python hello world.'])
    logger.info(results)
    return results


@pytest.mark.asyncio
async def test_custom_aio_session():
    logger.info("Start...")
    # 由于目前架设的https是自签署的，需要关闭ssl检验
    async with CustomAioSession():
        api = OpenAIGPTAPI()
        results = await try_hello(api)
        assert len(results) > 0
        results = await aask_batch(api)
        assert len(results) > 0
    logger.info("Done...")
