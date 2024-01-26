#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/6 14:13
@Author  : alexanderwu
@File    : llm_hello_world.py
"""
import asyncio
from pathlib import Path

from metagpt.llm import LLM
from metagpt.logs import logger
from metagpt.utils.common import encode_image


async def main():
    llm = LLM()
    logger.info(await llm.aask("hello world"))
    logger.info(await llm.aask_batch(["hi", "write python hello world."]))

    hello_msg = [{"role": "user", "content": "count from 1 to 10. split by newline."}]
    logger.info(await llm.acompletion(hello_msg))
    logger.info(await llm.acompletion_text(hello_msg))

    # streaming mode, much slower
    await llm.acompletion_text(hello_msg, stream=True)

    # check completion if exist to test llm complete functions
    if hasattr(llm, "completion"):
        logger.info(llm.completion(hello_msg))

    # check llm-vision capacity if it supports
    invoice_path = Path(__file__).parent.joinpath("..", "tests", "data", "invoices", "invoice-2.png")
    img_base64 = encode_image(invoice_path)
    try:
        res = await llm.aask(msg="if this is a invoice, just return True else return False",
                             images=[img_base64])
        assert "true" in res.lower()
    except Exception as exp:
        pass



if __name__ == "__main__":
    asyncio.run(main())
