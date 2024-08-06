#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/4/22 14:28
@Author  : alexanderwu
@File    : ping.py
"""

import asyncio

from metagpt.llm import LLM
from metagpt.logs import logger


async def ask_and_print(question: str, llm: LLM, system_prompt) -> str:
    logger.info(f"Q: {question}")
    rsp = await llm.aask(question, system_msgs=[system_prompt])
    logger.info(f"A: {rsp}")
    logger.info("\n")
    return rsp


async def main():
    llm = LLM()
    await ask_and_print("ping?", llm, "Just answer pong when ping.")


if __name__ == "__main__":
    asyncio.run(main())
