#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : test_write_test.py
"""
import pytest

from metagpt.actions.write_test import WriteTest
from metagpt.logs import logger
from metagpt.schema import Document, TestingContext


@pytest.mark.asyncio
async def test_write_test(context):
    code = """
    import random
    from typing import Tuple

    class Food:
        def __init__(self, position: Tuple[int, int]):
            self.position = position

        def generate(self, max_y: int, max_x: int):
            self.position = (random.randint(1, max_y - 1), random.randint(1, max_x - 1))
    """
    testing_context = TestingContext(filename="food.py", code_doc=Document(filename="food.py", content=code))
    write_test = WriteTest(i_context=testing_context, context=context)

    context = await write_test.run()
    logger.info(context.model_dump_json())

    # We cannot exactly predict the generated test cases, but we can check if it is a string and if it is not empty
    assert isinstance(context.test_doc.content, str)
    assert "from food import Food" in context.test_doc.content
    assert "class TestFood(unittest.TestCase)" in context.test_doc.content
    assert "def test_generate" in context.test_doc.content


@pytest.mark.asyncio
async def test_write_code_invalid_code(mocker, context):
    # Mock the _aask method to return an invalid code string
    mocker.patch.object(WriteTest, "_aask", return_value="Invalid Code String")

    # Create an instance of WriteTest
    write_test = WriteTest(context=context)

    # Call the write_code method
    code = await write_test.write_code("Some prompt:")

    # Assert that the returned code is the same as the invalid code string
    assert code == "Invalid Code String"


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
