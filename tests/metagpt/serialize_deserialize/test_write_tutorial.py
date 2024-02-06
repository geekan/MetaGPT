# -*- coding: utf-8 -*-
# @Desc    :
from typing import Dict

import pytest

from metagpt.actions.write_tutorial import WriteContent, WriteDirectory


@pytest.mark.asyncio
@pytest.mark.parametrize(("language", "topic"), [("English", "Write a tutorial about Python")])
async def test_write_directory_serdeser(language: str, topic: str, context):
    action = WriteDirectory(context=context)
    serialized_data = action.model_dump()
    assert serialized_data["name"] == "WriteDirectory"
    assert serialized_data["language"] == "Chinese"

    new_action = WriteDirectory(**serialized_data, context=context)
    ret = await new_action.run(topic=topic)
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
async def test_write_content_serdeser(language: str, topic: str, directory: Dict, context):
    action = WriteContent(language=language, directory=directory, context=context)
    serialized_data = action.model_dump()
    assert serialized_data["name"] == "WriteContent"

    new_action = WriteContent(**serialized_data, context=context)
    ret = await new_action.run(topic=topic)
    assert isinstance(ret, str)
    assert list(directory.keys())[0] in ret
    for value in list(directory.values())[0]:
        assert value in ret
