#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : write_test.py
"""
from metagpt.actions.action import Action


class WriteTest(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)
        self.code = None
        self.test_prompt_template = """
        Given the following code or function:
        {code}

        As a test engineer, please write appropriate test cases using Python's unittest framework to verify the correctness and robustness of this code.
        """

    async def run(self, code):
        self.code = code
        prompt = self.test_prompt_template.format(code=self.code)
        test_cases = await self._aask(prompt)
        return test_cases
