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
from typing import List

from loguru import logger as _logger
from pydantic import BaseModel, Field

from metagpt.const import METAGPT_ROOT
from metagpt.schema import BaseEnum


class ToolOutputItem(BaseModel):
    type_: str = Field(alias="type", default="str", description="Data type of `value` field.")
    name: str
    value: str


class ToolName(str, BaseEnum):
    Terminal = "Terminal"
    Plan = "Plan"
    Browser = "Browser"
    Files = "Files"
    WritePRD = "WritePRD"
    WriteDesign = "WriteDesign"
    WriteProjectPlan = "WriteProjectPlan"
    WriteCode = "WriteCode"
    WriteUntTest = "WriteUntTest"
    FixBug = "FixBug"
    GitArchive = "GitArchive"
    ImportRepo = "ImportRepo"


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


def log_tool_output(output: ToolOutputItem | List[ToolOutputItem], tool_name: str = ""):
    """interface for logging tool output, can be set to log tool output in different ways to different places with set_tool_output_logfunc"""
    if not _tool_output_log or not output:
        return

    outputs = output if isinstance(output, list) else [output]
    _tool_output_log(output=[i.model_dump() for i in outputs], tool_name=tool_name)


def set_llm_stream_logfunc(func):
    global _llm_stream_log
    _llm_stream_log = func


def set_tool_output_logfunc(func):
    global _tool_output_log
    _tool_output_log = func


_llm_stream_log = partial(print, end="")


_tool_output_log = partial(print, end="")
