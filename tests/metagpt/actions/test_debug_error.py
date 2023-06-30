#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:46
@Author  : alexanderwu
@File    : test_debug_error.py
"""
import pytest
from metagpt.actions.debug_error import DebugError


@pytest.mark.asyncio
async def test_debug_error():
    code = "def add(a, b):\n    return a - b"
    error = "AssertionError: Expected add(1, 1) to equal 2 but got 0"
    fixed_code = "def add(a, b):\n    return a + b"

    debug_error = DebugError("debug_error")

    result = await debug_error.run(code, error)

    prompt = f"以下是一段Python代码:\n\n{code}\n\n执行时发生了以下错误:\n\n{error}\n\n请尝试修复这段代码中的错误。"
    # mock_llm.ask.assert_called_once_with(prompt)
    assert len(result) > 0
