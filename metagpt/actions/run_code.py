#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:46
@Author  : alexanderwu
@File    : run_code.py
"""
import traceback

from metagpt.actions.action import Action


class RunCode(Action):
    def __init__(self, name, context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, code):
        try:
            # We will document_store the result in this dictionary
            namespace = {}
            exec(code, namespace)
            return namespace.get('result', None)
        except Exception as e:
            # If there is an error in the code, return the error message
            return traceback.format_exc()
