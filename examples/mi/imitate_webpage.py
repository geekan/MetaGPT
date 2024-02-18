#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/01/15
@Author  : mannaandpoem
@File    : imitate_webpage.py
"""
from metagpt.roles.mi.interpreter import Interpreter


async def main():
    web_url = "https://pytorch.org/"
    prompt = f"""This is a URL of webpage: '{web_url}' .
Firstly, utilize Selenium and WebDriver for rendering. 
Secondly, convert image to a webpage including HTML, CSS and JS in one go. 
Finally, save webpage in a text file. 
Note: All required dependencies and environments have been fully installed and configured."""
    mi = Interpreter(use_tools=True)

    await mi.run(prompt)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
