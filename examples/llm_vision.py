#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : example to run the ability of LLM vision

import asyncio
from pathlib import Path

from metagpt.llm import LLM
from metagpt.utils.common import encode_image


async def main():
    llm = LLM()

    # check if the configured llm supports llm-vision capacity. If not, it will throw a error
    invoice_path = Path(__file__).parent.joinpath("..", "tests", "data", "invoices", "invoice-2.png")
    img_base64 = encode_image(invoice_path)
    res = await llm.aask(msg="if this is a invoice, just return True else return False", images=[img_base64])
    assert "true" in res.lower()


if __name__ == "__main__":
    asyncio.run(main())
