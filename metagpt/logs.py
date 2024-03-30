#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/6/1 12:41
@Author  : alexanderwu
@File    : logs.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from functools import partial

from loguru import logger as _logger

from metagpt.const import METAGPT_ROOT


def define_log_level(print_level="INFO", logfile_level="DEBUG", name: str = None):
    """Adjust the log level to above level"""
    current_date = datetime.now()
    formatted_date = current_date.strftime("%Y%m%d")
    log_name = f"{name}_{formatted_date}" if name else formatted_date  # name a log with prefix name

    _logger.remove()
    _logger.add(sys.stderr, level=print_level)
    _logger.add(METAGPT_ROOT / f"logs/{log_name}.txt", level=logfile_level)
    return _logger


logger = define_log_level()


def log_llm_stream(msg):
    _llm_stream_log(msg)


def log_tool_output(output: dict, tool_name: str = ""):
    """interface for logging tool output, can be set to log tool output in different ways to different places with set_tool_output_logfunc"""
    _tool_output_log(output)


def set_llm_stream_logfunc(func):
    global _llm_stream_log
    _llm_stream_log = func


def set_tool_output_logfunc(func):
    global _tool_output_log
    _tool_output_log = func


_llm_stream_log = partial(print, end="")


_tool_output_log = partial(print, end="")
