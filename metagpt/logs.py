#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/6/1 12:41
@Author  : alexanderwu
@File    : logs.py
"""

from __future__ import annotations

import asyncio
import inspect
import sys
from contextvars import ContextVar
from datetime import datetime
from functools import partial
from typing import Any

from loguru import logger as _logger
from pydantic import BaseModel, Field

from metagpt.const import METAGPT_ROOT

LLM_STREAM_QUEUE: ContextVar[asyncio.Queue] = ContextVar("llm-stream")


class ToolLogItem(BaseModel):
    type_: str = Field(alias="type", default="str", description="Data type of `value` field.")
    name: str
    value: Any


TOOL_LOG_END_MARKER = ToolLogItem(
    type="str", name="end_marker", value="\x18\x19\x1B\x18"
)  # A special log item to suggest the end of a stream log

_print_level = "INFO"


def define_log_level(print_level="INFO", logfile_level="DEBUG", name: str = None):
    """Adjust the log level to above level"""
    global _print_level
    _print_level = print_level

    current_date = datetime.now()
    formatted_date = current_date.strftime("%Y%m%d")
    log_name = f"{name}_{formatted_date}" if name else formatted_date  # name a log with prefix name

    _logger.remove()
    _logger.add(sys.stderr, level=print_level)
    _logger.add(METAGPT_ROOT / f"logs/{log_name}.txt", level=logfile_level)
    return _logger


logger = define_log_level()


def log_llm_stream(msg):
    """
    Logs a message to the LLM stream.

    Args:
        msg: The message to be logged.

    Notes:
        If the LLM_STREAM_QUEUE has not been set (e.g., if `create_llm_stream_queue` has not been called),
        the message will not be added to the LLM stream queue.
    """

    queue = get_llm_stream_queue()
    if queue:
        queue.put_nowait(msg)
    _llm_stream_log(msg)


def log_tool_output(output: ToolLogItem | list[ToolLogItem], tool_name: str = ""):
    """interface for logging tool output, can be set to log tool output in different ways to different places with set_tool_output_logfunc"""
    _tool_output_log(output=output, tool_name=tool_name)


async def log_tool_output_async(output: ToolLogItem | list[ToolLogItem], tool_name: str = ""):
    """async interface for logging tool output, used when output contains async object"""
    await _tool_output_log_async(output=output, tool_name=tool_name)


async def get_human_input(prompt: str = ""):
    """interface for getting human input, can be set to get input from different sources with set_human_input_func"""
    if inspect.iscoroutinefunction(_get_human_input):
        return await _get_human_input(prompt)
    else:
        return _get_human_input(prompt)


def set_llm_stream_logfunc(func):
    global _llm_stream_log
    _llm_stream_log = func


def set_tool_output_logfunc(func):
    global _tool_output_log
    _tool_output_log = func


async def set_tool_output_logfunc_async(func):
    # async version
    global _tool_output_log_async
    _tool_output_log_async = func


def set_human_input_func(func):
    global _get_human_input
    _get_human_input = func


_llm_stream_log = partial(print, end="")


_tool_output_log = (
    lambda *args, **kwargs: None
)  # a dummy function to avoid errors if set_tool_output_logfunc is not called


async def _tool_output_log_async(*args, **kwargs):
    # async version
    pass


def create_llm_stream_queue():
    """Creates a new LLM stream queue and sets it in the context variable.

    Returns:
        The newly created asyncio.Queue instance.
    """
    queue = asyncio.Queue()
    LLM_STREAM_QUEUE.set(queue)
    return queue


def get_llm_stream_queue():
    """Retrieves the current LLM stream queue from the context variable.

    Returns:
        The asyncio.Queue instance if set, otherwise None.
    """
    return LLM_STREAM_QUEUE.get(None)


_get_human_input = input  # get human input from console by default


def _llm_stream_log(msg):
    if _print_level in ["INFO"]:
        print(msg, end="")
