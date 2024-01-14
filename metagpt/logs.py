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

from loguru import logger as _logger

from metagpt.const import METAGPT_ROOT


def define_log_level(print_level="INFO", logfile_level="DEBUG"):
    """Adjust the log level to above level"""
    current_date = datetime.now()
    formatted_date = current_date.strftime("%Y%m%d")

    _logger.remove()
    _logger.add(sys.stderr, level=print_level)
    _logger.add(METAGPT_ROOT / f"logs/{formatted_date}.txt", level=logfile_level)
    return _logger


logger = define_log_level()


def log_llm_stream(msg):
    _llm_stream_log(msg)


def set_llm_stream_logfunc(func):
    global _llm_stream_log
    _llm_stream_log = func


_llm_stream_log = partial(print, end="")
