#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/15
@Author  : mannaandpoem
@File    : imitate_webpage.py
"""
from metagpt.roles.di.data_interpreter import DataInterpreter


async def main():
    web_url = "https://pytorch.org/"
    prompt = f"""This is a URL of webpage: '{web_url}' .
Firstly, utilize Selenium and WebDriver for rendering. 
Secondly, convert image to a webpage including HTML, CSS and JS in one go.
Note: All required dependencies and environments have been fully installed and configured."""
    di = DataInterpreter(tools=["GPTvGenerator"])

    await di.run(prompt)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
