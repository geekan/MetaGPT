#!/usr/bin/env python

import asyncio
from metagpt.actions.data_analyse import DataAnalyse


async def main():
    file_path = "../tests/data/data_for_test.csv"
    context = "Analyze loans of different ages and educational backgrounds"
    outs, errs = await DataAnalyse().run(context, file_path)
    print(f"save resutl to worksparce.")


if __name__ == '__main__':
    asyncio.run(main())
