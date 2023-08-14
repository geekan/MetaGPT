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
async def test_run_text():
    result, errs = await RunCode.run_text("result = 1 + 1")
    assert result == 2
    assert errs == ""

    result, errs = await RunCode.run_text("result = 1 / 0")
    assert result == ""
    assert "ZeroDivisionError" in errs


@pytest.mark.asyncio
async def test_run_script():
    # Successful command
    out, err = await RunCode.run_script(".", command=["echo", "Hello World"])
    assert out.strip() == "Hello World"
    assert err == ""

    # Unsuccessful command
    out, err = await RunCode.run_script(".", command=["python", "-c", "print(1/0)"])
    assert "ZeroDivisionError" in err


@pytest.mark.asyncio
async def test_run():
    action = RunCode()
    result = await action.run(mode="text", code="print('Hello, World')")
    assert "PASS" in result

    result = await action.run(
        mode="script",
        code="echo 'Hello World'",
        code_file_name="",
        test_code="",
        test_file_name="",
        command=["echo", "Hello World"],
        working_directory=".",
        additional_python_paths=[],
    )
    assert "PASS" in result


@pytest.mark.asyncio
async def test_run_failure():
    action = RunCode()
    result = await action.run(mode="text", code="result = 1 / 0")
    assert "FAIL" in result

    result = await action.run(
        mode="script",
        code='python -c "print(1/0)"',
        code_file_name="",
        test_code="",
        test_file_name="",
        command=["python", "-c", "print(1/0)"],
        working_directory=".",
        additional_python_paths=[],
    )
    assert "FAIL" in result
