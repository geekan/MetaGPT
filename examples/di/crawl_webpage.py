# -*- encoding: utf-8 -*-
"""
@Date    :   2024/01/24 15:11:27
@Author  :   orange-crow
@File    :   crawl_webpage.py
"""

from metagpt.roles.di.data_interpreter import DataInterpreter


async def main():
    prompt = """Get data from `paperlist` table in https://papercopilot.com/statistics/iclr-statistics/iclr-2024-statistics/,
    and save it to a csv file. paper title must include `multiagent` or `large language model`. *notice: print key variables*"""
    di = DataInterpreter(use_tools=True)

    await di.run(prompt)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
