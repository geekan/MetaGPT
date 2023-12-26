#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/20
@Author  : mashenquan
@File    : test_rebuild_class_view.py
@Desc    : Unit tests for rebuild_class_view.py
"""
from pathlib import Path

import pytest

from metagpt.actions.rebuild_class_view import RebuildClassView
from metagpt.llm import LLM


@pytest.mark.asyncio
async def test_rebuild():
    action = RebuildClassView(name="RedBean", context=Path(__file__).parent.parent, llm=LLM())
    await action.run()


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
