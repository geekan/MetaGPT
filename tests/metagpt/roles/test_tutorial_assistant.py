#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2023/9/6 23:11:27
@Author  : Stitch-z
@File    : test_tutorial_assistant.py
"""

import pytest

from metagpt.const import TUTORIAL_PATH
from metagpt.roles.tutorial_assistant import TutorialAssistant
from metagpt.utils.common import aread


@pytest.mark.asyncio
@pytest.mark.parametrize(("language", "topic"), [("Chinese", "Write a tutorial about pip")])
async def test_tutorial_assistant(language: str, topic: str, context):
    role = TutorialAssistant(language=language, context=context)
    msg = await role.run(topic)
    assert TUTORIAL_PATH.exists()
    filename = msg.content
    content = await aread(filename=filename)
    assert "pip" in content


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
