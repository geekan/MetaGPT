#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : parse record to generate learned standard operations in stage=learn & mode=manual, LIKE scripts/document_generation.py

from metagpt.actions.action import Action

from examples.andriod_assistant.prompts.operation_prompt import *

class ParseRecord(Action):
    name: str = "ParseRecord"

    async def run(self):
        pass
