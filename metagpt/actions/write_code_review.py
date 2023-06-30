#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : write_code_review.py
"""

from metagpt.actions.action import Action

PROMPT_TEMPLATE = """
Please review the following code:
{code}

The main aspects you need to focus on include but are not limited to the code structure, coding standards, possible errors, and improvement suggestions.

Please write your code review:
"""


class WriteCodeReview(Action):
    def __init__(self, name, context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, code):
        """
        Generate a code review for the given code.

        :param code: The code to be reviewed.
        :type code: str
        :return: The code review.
        :rtype: str
        """
        # Set the context for the llm model
        self.context = {"code": code}

        # Generate the prompt
        prompt = PROMPT_TEMPLATE.format(**self.context)

        # Generate the code review
        self.input_data = prompt
        self.output_data = await self._aask(prompt)

        return self.output_data
