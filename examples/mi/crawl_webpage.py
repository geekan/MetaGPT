# -*- encoding: utf-8 -*-
"""
@Date    :   2024/01/24 15:11:27
@Author  :   orange-crow
@File    :   crawl_webpage.py
"""

from metagpt.roles.mi.interpreter import Interpreter


async def main():
    prompt = """Get data from `paperlist` table in https://papercopilot.com/statistics/iclr-statistics/iclr-2024-statistics/,
    and save it to a csv file. paper title must include `multiagent` or `large language model`. *notice: print key variables*"""
    mi = Interpreter(use_tools=True)

    await mi.run(prompt)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
