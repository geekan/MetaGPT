#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/13 12:26
# @Author  : femto Zheng
# @File    : execute_task.py


from metagpt.actions import Action
from metagpt.schema import Message


class ExecuteTask(Action):
    """ExecuteTask is an action for executing tasks.

    Attributes:
        name: The name of the action.
        i_context: The initial context provided as a list of messages.
    """

    name: str = "ExecuteTask"
    i_context: list[Message] = []

    async def run(self, *args, **kwargs):
        pass
