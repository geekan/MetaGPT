#!/usr/bin/env python3
# _*_ coding: utf-8 _*_
"""
@Time    : 2023/9/6 21:41:34
@Author  : Stitch-z
@File    : test_write_tutorial.py
"""
from typing import Dict

import pytest

from metagpt.actions.write_tutorial import WriteContent, WriteDirectory


@pytest.mark.asyncio
@pytest.mark.parametrize(("language", "topic"), [("English", "Write a tutorial about Python")])
async def test_write_directory(language: str, topic: str, context):
    ret = await WriteDirectory(language=language, context=context).run(topic=topic)
    assert isinstance(ret, dict)
    assert "title" in ret
    assert "directory" in ret
    assert isinstance(ret["directory"], list)
    assert len(ret["directory"])
    assert isinstance(ret["directory"][0], dict)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("language", "topic", "directory"),
    [("English", "Write a tutorial about Python", {"Introduction": ["What is Python?", "Why learn Python?"]})],
)
async def test_write_content(language: str, topic: str, directory: Dict, context):
    ret = await WriteContent(language=language, directory=directory, context=context).run(topic=topic)
    assert isinstance(ret, str)
    assert list(directory.keys())[0] in ret
    for value in list(directory.values())[0]:
        assert value in ret
