#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/6/1 12:41
@Author  : alexanderwu
@File    : logs.py
"""

import sys
from datetime import datetime
from functools import partial
from typing import Callable, Optional

from loguru import logger as _logger

from metagpt.const import METAGPT_ROOT


def define_log_level(print_level: str = "INFO", logfile_level: str = "DEBUG", name: Optional[str] = None) -> _logger:
    """Adjust the log level to the specified levels."""
    current_date = datetime.now()
    formatted_date = current_date.strftime("%Y%m%d")
    log_name = f"{name}_{formatted_date}" if name else formatted_date  # name a log with prefix name

    _logger.remove()
    _logger.add(sys.stderr, level=print_level)
    _logger.add(METAGPT_ROOT / f"logs/{log_name}.txt", level=logfile_level)
    return _logger


logger = define_log_level()


def log_llm_stream(msg: str) -> None:
    """Log LLM stream messages."""
    _llm_stream_log(msg)


def set_llm_stream_logfunc(func: Callable[[str], None]) -> None:
    """Set the function to be used for logging LLM streams."""
    global _llm_stream_log
    _llm_stream_log = func


_llm_stream_log: Callable[[str], None] = partial(print, end="")
