#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2023/9/6 23:11:27
@Author  : Stitch-z
@File    : test_tutorial_assistant.py
"""
import shutil

import pytest

from metagpt.const import TUTORIAL_PATH
from metagpt.roles.tutorial_assistant import TutorialAssistant


@pytest.mark.asyncio
@pytest.mark.parametrize(("language", "topic"), [("Chinese", "Write a tutorial about Python")])
async def test_tutorial_assistant(language: str, topic: str):
    shutil.rmtree(path=TUTORIAL_PATH, ignore_errors=True)

    topic = "Write a tutorial about MySQL"
    role = TutorialAssistant(language=language)
    msg = await role.run(topic)
    assert "MySQL" in msg.content
    assert TUTORIAL_PATH.exists()
    # filename = msg.content
    # title = filename.split("/")[-1].split(".")[0]
    # async with aiofiles.open(filename, mode="r") as reader:
    #     content = await reader.read()
    #     assert content.startswith(f"# {title}")


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
