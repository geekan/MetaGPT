#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/26 14:27
@Author  : zhanglei
@File    : moderation.py
"""
import asyncio
from typing import Union

from metagpt.llm import LLM


class Moderation:
    def __init__(self):
        self.llm = LLM()

    async def amoderation(self, content: Union[str, list[str]]):
        resp = []
        if content:
            moderation_results = await self.llm.amoderation(content=content)
            results = moderation_results.results
            for item in results:
                resp.append(item.flagged)

        return resp


async def main():
    moderation = Moderation()
    rsp = await moderation.amoderation(
        content=["I will kill you", "The weather is really nice today", "I want to hit you"]
    )
    print(rsp)


if __name__ == "__main__":
    asyncio.run(main())
