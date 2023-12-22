#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18
@Author  : mashenquan
@File    : test_text_to_speech.py
@Desc    : Unit tests.
"""
import asyncio
import base64

from pydantic import BaseModel

from metagpt.learn.text_to_speech import text_to_speech


async def mock_text_to_speech():
    class Input(BaseModel):
        input: str

    inputs = [{"input": "Panda emoji"}]

    for i in inputs:
        seed = Input(**i)
        base64_data = await text_to_speech(seed.input)
        assert base64_data != ""
        print(f"{seed.input} -> {base64_data}")
        flags = ";base64,"
        assert flags in base64_data
        ix = base64_data.find(flags) + len(flags)
        declaration = base64_data[0:ix]
        assert declaration
        data = base64_data[ix:]
        assert data
        assert base64.b64decode(data, validate=True)


def test_suite():
    loop = asyncio.get_event_loop()
    task = loop.create_task(mock_text_to_speech())
    loop.run_until_complete(task)


if __name__ == "__main__":
    test_suite()
