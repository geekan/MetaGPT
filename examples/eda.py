#!/usr/bin/env python

import asyncio

from metagpt.actions.data_analyse import DataAnalyse


async def main():
    file_path = "/Users/rain/Desktop/code/aigc/MetaGPT/tests/data/data_for_test.csv"
    context = "Which are the 5 happiest countries?"
    role = DataAnalyse()
    await role.run(context, file_path)
    # print(f"save report to {RESEARCH_PATH / f'{topic}.md'}.")


if __name__ == '__main__':
    asyncio.run(main())
