#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/6 14:13
@Author  : alexanderwu
@File    : llm_hello_world.py
"""
import asyncio

from metagpt.logs import logger
from metagpt.llm import LLM


async def main():
    llm = LLM()

    logger.info(await llm.aask('hello world'))
    logger.info(await llm.aask_batch(['hi', 'write python hello world.']))

    hello_msg = [{'role': 'user', 'content': 'hello'}]
    logger.info(await llm.acompletion(hello_msg))
    logger.info(await llm.acompletion_batch([hello_msg]))
    logger.info(await llm.acompletion_batch_text([hello_msg]))


if __name__ == '__main__':
    asyncio.run(main())
