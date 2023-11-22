#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/13 12:26
@Author  : femto Zheng
@File    : execute_task.py
"""
from metagpt.actions import Action
from metagpt.schema import Message


class ExecuteTask(Action):
    def __init__(self, name="ExecuteTask", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)

    def run(self, *args, **kwargs):
        pass
