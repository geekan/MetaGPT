#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/13 12:26
@Author  : femto Zheng
@File    : execute_task.py
"""

from pydantic import Field

from metagpt.actions import Action
from metagpt.llm import LLM
from metagpt.provider.base_llm import BaseLLM
from metagpt.schema import Message


class ExecuteTask(Action):
    name: str = "ExecuteTask"
    context: list[Message] = []
    llm: BaseLLM = Field(default_factory=LLM, exclude=True)

    async def run(self, *args, **kwargs):
        pass
