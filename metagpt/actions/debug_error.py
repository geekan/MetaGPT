#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:46
@Author  : alexanderwu
@File    : debug_error.py
"""
from metagpt.actions.action import Action


class DebugError(Action):
    def __init__(self, name, context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, code, error):
        prompt = f"Here is a piece of Python code:\n\n{code}\n\nThe following error occurred during execution:" \
                 f"\n\n{error}\n\nPlease try to fix the error in this code."
        fixed_code = await self._aask(prompt)
        return fixed_code
