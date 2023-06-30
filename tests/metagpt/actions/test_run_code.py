#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:46
@Author  : alexanderwu
@File    : test_run_code.py
"""
import pytest
from metagpt.actions.run_code import RunCode


@pytest.mark.asyncio
async def test_run_code():
    code = """
def add(a, b):
    return a + b
result = add(1, 2)
"""
    run_code = RunCode("run_code")

    result = await run_code.run(code)

    assert result == 3


@pytest.mark.asyncio
async def test_run_code_with_error():
    code = """
def add(a, b):
    return a + b
result = add(1, '2')
"""
    run_code = RunCode("run_code")

    result = await run_code.run(code)

    assert "TypeError: unsupported operand type(s) for +" in result

