#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : summarize the content of agents' conversation

from metagpt.actions.action import Action
from metagpt.schema import Message


class SummarizeConv(Action):

    def __init__(self, name="SummarizeConv", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)
