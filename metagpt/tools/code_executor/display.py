# -*- encoding: utf-8 -*-
"""
@Date    :   2024/11/13 22:07:28
@Author  :   orange-crow
@File    :   display.py
"""

import asyncio

from rich.console import Console, Group
from rich.live import Live
from rich.syntax import Syntax
from rich.text import Text


async def print_pycode_live(code: str, delay: float = 0.15):
    """
    在终端上实时打印代码，使用特定的风格突出显示代码。

    :param code: 要打印的代码字符串
    :param delay: 每次打印的延迟时间（秒）
    """
    syntax_lines = []
    with Live(auto_refresh=False, console=Console(), vertical_overflow="visible") as live:
        for i, line in enumerate(code.splitlines()):
            syntax = Syntax(line, "python", theme="monokai", line_numbers=True, start_line=i + 1)
            syntax_lines.append(syntax)
            live.update(Group(*syntax_lines))
            live.refresh()
            await asyncio.sleep(delay)


async def print_text_live(text: str, level: str = "STDOUT", delay: float = 0.15):
    """
    在终端上实时打印文本，使用特定的风格突出显示文本。

    :param text: 要打印的文本字符串
    :param delay: 每次打印的延迟时间（秒）
    """
    text_objs = []
    styles = {"STDOUT": "bold white on blue", "STDERR": "bold white on yellow"}
    with Live(auto_refresh=False, console=Console(), vertical_overflow="visible") as live:
        for line in text.splitlines():
            text_obj = Text(line, style=styles[level])
            text_objs.append(text_obj)
            live.update(Group(*text_objs))
            live.refresh()
            await asyncio.sleep(delay)
