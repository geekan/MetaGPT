#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/17 10:24
# @Author  : lidanyang
# @File    : test_register.py
# @Desc    :
import pytest

from metagpt.tools.functions.register.register import FunctionRegistry
from metagpt.tools.functions.schemas.base import ToolSchema, field


@pytest.fixture
def registry():
    return FunctionRegistry()


class AddNumbers(ToolSchema):
    """Add two numbers"""

    num1: int = field(description="First number")
    num2: int = field(description="Second number")


def test_register(registry):
    @registry.register("module1", AddNumbers)
    def add_numbers(num1, num2):
        return num1 + num2

    assert len(registry.functions["module1"]) == 1
    assert "add_numbers" in registry.functions["module1"]

    with pytest.raises(ValueError):

        @registry.register("module1", AddNumbers)
        def add_numbers(num1, num2):
            return num1 + num2

    func = registry.get("module1", "add_numbers")
    assert func["func"](1, 2) == 3
    assert func["schema"] == {
        "name": "add_numbers",
        "description": "Add two numbers",
        "parameters": {
            "type": "object",
            "properties": {
                "num1": {"description": "First number", "type": "int"},
                "num2": {"description": "Second number", "type": "int"},
            },
            "required": ["num1", "num2"],
        },
    }

    module1_funcs = registry.get_all_by_module("module1")
    assert len(module1_funcs) == 1
