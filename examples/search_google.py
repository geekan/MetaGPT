#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/7 18:32
@Author  : alexanderwu
@File    : search_google.py
"""

import asyncio

from metagpt.roles import Searcher


async def main():
    await Searcher().run("What are some good sun protection products?")


if __name__ == "__main__":
    asyncio.run(main())
