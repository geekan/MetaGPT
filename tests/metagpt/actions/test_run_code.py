#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:46
@Author  : alexanderwu
@File    : test_run_code.py
@Modifiled By: mashenquan, 2023-12-6. According to RFC 135
"""
import pytest

from metagpt.actions.run_code import RunCode
from metagpt.schema import RunCodeContext


@pytest.mark.asyncio
async def test_run_text():
    out, err = await RunCode.run_text("result = 1 + 1")
    assert out == 2
    assert err == ""

    out, err = await RunCode.run_text("result = 1 / 0")
    assert out == ""
    assert "division by zero" in err


@pytest.mark.asyncio
async def test_run_script(context):
    # Successful command
    out, err = await RunCode(context=context).run_script(".", command=["echo", "Hello World"])
    assert out.strip() == "Hello World"
    assert err == ""

    # Unsuccessful command
    out, err = await RunCode(context=context).run_script(".", command=["python", "-c", "print(1/0)"])
    assert "ZeroDivisionError" in err


@pytest.mark.asyncio
async def test_run(context):
    inputs = [
        (RunCodeContext(mode="text", code_filename="a.txt", code="result = 'helloworld'"), "PASS"),
        (
            RunCodeContext(
                mode="script",
                code_filename="a.sh",
                code="echo 'Hello World'",
                command=["echo", "Hello World"],
                working_directory=".",
            ),
            "PASS",
        ),
        (
            RunCodeContext(
                mode="script",
                code_filename="a.py",
                code='python -c "print(1/0)"',
                command=["python", "-c", "print(1/0)"],
                working_directory=".",
            ),
            "FAIL",
        ),
    ]
    for ctx, result in inputs:
        rsp = await RunCode(i_context=ctx, context=context).run()
        assert result in rsp.summary
