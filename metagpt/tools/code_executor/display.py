# -*- encoding: utf-8 -*-
"""
@Date    :   2024/11/13 22:07:28
@Author  :   orange-crow
@File    :   display.py
"""

import asyncio
from typing import Literal

from rich.console import Console, Group
from rich.live import Live
from rich.syntax import Syntax
from rich.text import Text


async def print_pycode_live(code: str, delay: float = 0.15):
    """
    Asynchronously prints Python code line by line with syntax highlighting in the terminal.

    Args:
        code (str): The Python code to be printed.
        delay (float, optional): The delay between printing each line in seconds. Defaults to 0.15.

    Returns:
        None
    """
    syntax_lines = []
    with Live(auto_refresh=False, console=Console(), vertical_overflow="visible") as live:
        for i, line in enumerate(code.splitlines()):
            syntax = Syntax(line, "python", theme="monokai", line_numbers=True, start_line=i + 1)
            syntax_lines.append(syntax)
            live.update(Group(*syntax_lines))
            live.refresh()
            await asyncio.sleep(delay)


async def print_text_live(text: str, level: Literal["STDOUT", "STDERR"] = "STDOUT", delay: float = 0.15):
    """
    Asynchronously prints text line by line with specified style in the terminal.

    Args:
        text (str): The text to be printed.
        level (str, optional): The log level, which determines the text style. Defaults to "STDOUT".
        delay (float, optional): The delay between printing each line in seconds. Defaults to 0.15.

    Returns:
        None
    """
    text_objs = []
    styles = {"STDOUT": "bold white on blue", "STDERR": "bold white on yellow"}
    with Live(auto_refresh=False, console=Console(), vertical_overflow="visible") as live:
        for line in text.splitlines():
            if line != "END_OF_EXECUTION":
                text_obj = Text(line, style=styles[level])
                text_objs.append(text_obj)
                live.update(Group(*text_objs))
                live.refresh()
                await asyncio.sleep(delay)
