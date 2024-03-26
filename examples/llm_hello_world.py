#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/6 14:13
@Author  : alexanderwu
@File    : llm_hello_world.py
"""
import asyncio

from metagpt.llm import LLM
from metagpt.logs import logger


async def main():
    llm = LLM()
    # llm type check
    question = "what's your name"
    logger.info(f"{question}: ")
    logger.info(await llm.aask(question))
    logger.info("\n\n")

    logger.info(
        await llm.aask(
            "who are you", system_msgs=["act as a robot, just answer 'I'am robot' if the question is 'who are you'"]
        )
    )

    logger.info(await llm.aask_batch(["hi", "write python hello world."]))

    hello_msg = [{"role": "user", "content": "count from 1 to 10. split by newline."}]
    logger.info(await llm.acompletion(hello_msg))
    logger.info(await llm.acompletion_text(hello_msg))

    # streaming mode, much slower
    await llm.acompletion_text(hello_msg, stream=True)

    # check completion if exist to test llm complete functions
    if hasattr(llm, "completion"):
        logger.info(llm.completion(hello_msg))


if __name__ == "__main__":
    asyncio.run(main())
