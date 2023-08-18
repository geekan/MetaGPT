#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/18
@Author  : mashenquan
@File    : test_text_to_embedding.py
@Desc    : Unit tests.
"""

import asyncio
import base64

from pydantic import BaseModel

from metagpt.learn.text_to_embedding import text_to_embedding


async def mock_text_to_embedding():
    class Input(BaseModel):
        input: str

    inputs = [
        {"input": "Panda emoji"}
    ]

    for i in inputs:
        seed = Input(**i)
        data = text_to_embedding(seed.input)
        v = ResultEmbedding(**data)
        assert len(v.data) > 0


def test_suite():
    loop = asyncio.get_event_loop()
    task = loop.create_task(mock_text_to_embedding())
    loop.run_until_complete(task)


if __name__ == '__main__':
    test_suite()
