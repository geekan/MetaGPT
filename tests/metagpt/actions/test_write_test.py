#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : test_write_test.py
"""
import pytest
from metagpt.logs import logger
from metagpt.actions.write_test import WriteTest


@pytest.mark.asyncio
async def test_write_test():
    code = """
    def add(a, b):
        return a + b
    """

    write_test = WriteTest("write_test")

    test_cases = await write_test.run(code)

    # We cannot exactly predict the generated test cases, but we can check if it is a string and if it is not empty
    assert isinstance(test_cases, str)
    assert len(test_cases) > 0
