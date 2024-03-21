#!/usr/bin/env python
# -*- coding: utf-8 -*-
from metagpt.roles.di.data_interpreter import DataInterpreter


async def main():
    template = "https://arxiv.org/list/{tag}/pastweek?skip=0&show=300"
    tags = ["cs.ai", "cs.cl", "cs.lg", "cs.se"]
    urls = [template.format(tag=tag) for tag in tags]
    prompt = f"""This is a collection of arxiv urls: '{urls}' .
Record each article, remove duplicates by title (they may have multiple tags), filter out papers related to 
large language model / agent / llm, print top 100 and visualize the word count of the titles"""
    di = DataInterpreter(react_mode="react", tools=["scrape_web_playwright"])

    await di.run(prompt)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
