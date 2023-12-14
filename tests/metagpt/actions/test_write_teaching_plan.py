#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/7/28 17:25
@Author  : mashenquan
@File    : test_write_teaching_plan.py
"""

import asyncio
from typing import Optional

from langchain.llms.base import LLM
from pydantic import BaseModel

from metagpt.actions.write_teaching_plan import WriteTeachingPlanPart
from metagpt.config import Config
from metagpt.schema import Message


class MockWriteTeachingPlanPart(WriteTeachingPlanPart):
    def __init__(self, options, name: str = "", context=None, llm: LLM = None, topic="", language="Chinese"):
        super().__init__(options, name, context, llm, topic, language)

    async def _aask(self, prompt: str, system_msgs: Optional[list[str]] = None) -> str:
        return f"{WriteTeachingPlanPart.DATA_BEGIN_TAG}\nprompt\n{WriteTeachingPlanPart.DATA_END_TAG}"


async def mock_write_teaching_plan_part():
    class Inputs(BaseModel):
        input: str
        name: str
        topic: str
        language: str

    inputs = [
        {"input": "AABBCC", "name": "A", "topic": WriteTeachingPlanPart.COURSE_TITLE, "language": "C"},
        {"input": "DDEEFFF", "name": "A1", "topic": "B1", "language": "C1"},
    ]

    for i in inputs:
        seed = Inputs(**i)
        options = Config().runtime_options
        act = MockWriteTeachingPlanPart(options=options, name=seed.name, topic=seed.topic, language=seed.language)
        await act.run([Message(content="")])
        assert act.topic == seed.topic
        assert str(act) == seed.topic
        assert act.name == seed.name
        assert act.rsp == "# prompt" if seed.topic == WriteTeachingPlanPart.COURSE_TITLE else "prompt"


def test_suite():
    loop = asyncio.get_event_loop()
    task = loop.create_task(mock_write_teaching_plan_part())
    loop.run_until_complete(task)


if __name__ == "__main__":
    test_suite()
