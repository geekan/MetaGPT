#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/7/28 17:25
@Author  : mashenquan
@File    : test_write_teaching_plan.py
"""

import pytest

from metagpt.actions.write_teaching_plan import WriteTeachingPlanPart


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("topic", "context"),
    [("Title", "Lesson 1: Learn to draw an apple."), ("Teaching Content", "Lesson 1: Learn to draw an apple.")],
)
@pytest.mark.usefixtures("llm_mock")
async def test_write_teaching_plan_part(topic, context):
    action = WriteTeachingPlanPart(topic=topic, context=context)
    rsp = await action.run()
    assert rsp


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
