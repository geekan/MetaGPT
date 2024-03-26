# -*- encoding: utf-8 -*-
"""
@Date    :   2024/01/24 15:11:27
@Author  :   orange-crow
@File    :   crawl_webpage.py
"""

from metagpt.roles.di.data_interpreter import DataInterpreter

PAPER_LIST_REQ = """"
Get data from `paperlist` table in https://papercopilot.com/statistics/iclr-statistics/iclr-2024-statistics/,
and save it to a csv file. paper title must include `multiagent` or `large language model`. *notice: print key variables*
"""

ECOMMERCE_REQ = """
Get products data from website https://scrapeme.live/shop/ and save it as a csv file.
**Notice: Firstly parse the web page encoding and the text HTML structure;
The first page product name, price, product URL, and image URL must be saved in the csv;**
"""

NEWS_36KR_REQ = """从36kr创投平台https://pitchhub.36kr.com/financing-flash 所有初创企业融资的信息, **注意: 这是一个中文网站**;
下面是一个大致流程, 你会根据每一步的运行结果对当前计划中的任务做出适当调整:
1. 爬取并本地保存html结构;
2. 直接打印第7个*`快讯`*关键词后2000个字符的html内容, 作为*快讯的html内容示例*;
3. 反思*快讯的html内容示例*中的规律, 设计正则匹配表达式来获取*`快讯`*的标题、链接、时间;
4. 筛选最近3天的初创企业融资*`快讯`*, 以list[dict]形式打印前5个。
5. 将全部结果存在本地csv中
"""


async def main():
    di = DataInterpreter(tools=["scrape_web_playwright"])

    await di.run(ECOMMERCE_REQ)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
