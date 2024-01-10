#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

"""
@Time    : 2023/9/4 21:40:57
@Author  : Stitch-z
@File    : tutorial_assistant.py
"""

import asyncio

from metagpt.roles.tutorial_assistant import TutorialAssistant


async def main():
    topic = "Write a tutorial about MySQL"
    role = TutorialAssistant(language="Chinese")
    await role.run(topic)


if __name__ == "__main__":
    asyncio.run(main())
