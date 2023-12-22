#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/27
@Author  : mashenquan
@File    : test_brain_memory.py
"""
import json
from typing import List

import pydantic

from metagpt.memory.brain_memory import BrainMemory
from metagpt.schema import Message


def test_json():
    class Input(pydantic.BaseModel):
        history: List[str]
        solution: List[str]
        knowledge: List[str]
        stack: List[str]

    inputs = [{"history": ["a", "b"], "solution": ["c"], "knowledge": ["d", "e"], "stack": ["f"]}]

    for i in inputs:
        v = Input(**i)
        bm = BrainMemory()
        for h in v.history:
            msg = Message(content=h)
            bm.history.append(msg.dict())
        for h in v.solution:
            msg = Message(content=h)
            bm.solution.append(msg.dict())
        for h in v.knowledge:
            msg = Message(content=h)
            bm.knowledge.append(msg.dict())
        for h in v.stack:
            msg = Message(content=h)
            bm.stack.append(msg.dict())
        s = bm.json()
        m = json.loads(s)
        bm = BrainMemory(**m)
        assert bm
        for v in bm.history:
            msg = Message(**v)
            assert msg


if __name__ == "__main__":
    test_json()
