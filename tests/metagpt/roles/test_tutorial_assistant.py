#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2023/9/6 23:11:27
@Author  : Stitch-z
@File    : test_tutorial_assistant.py
"""
import aiofiles
import pytest

from metagpt.roles.tutorial_assistant import TutorialAssistant


@pytest.mark.asyncio
@pytest.mark.parametrize(("language", "topic"), [("Chinese", "Write a tutorial about pip")])
async def test_tutorial_assistant(language: str, topic: str):
    role = TutorialAssistant(language=language)
    msg = await role.run(topic)
    filename = msg.content
    async with aiofiles.open(filename, mode="r", encoding="utf-8") as reader:
        content = await reader.read()
        assert content

