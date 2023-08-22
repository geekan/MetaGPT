#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/7 18:32
@Author  : alexanderwu
@File    : search_google.py
@Modified By: mashenquan, 2023-8-9, fix-bug: cannot find metagpt module.
"""

import asyncio
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from metagpt.roles import Searcher


async def main():
    await Searcher().run("What are some good sun protection products?")


if __name__ == '__main__':
    asyncio.run(main())
