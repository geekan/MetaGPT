#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/3/22 10:54
@Author  : alexanderwu
@File    : custom_tool.py
"""

from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.tools.tool_registry import register_tool


@register_tool()
def magic_function(arg1: str, arg2: int) -> dict:
    """
    The magic function that does something.

    Args:
        arg1 (str): ...
        arg2 (int): ...

    Returns:
        dict: ...
    """
    return {"arg1": arg1 * 3, "arg2": arg2 * 5}


async def main():
    di = DataInterpreter(tools=["magic_function"])
    await di.run("Just call the magic function with arg1 'A' and arg2 2. Tell me the result.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
