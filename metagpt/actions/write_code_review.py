#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : write_code_review.py
"""

from metagpt.actions.action import Action
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.utils.common import CodeParser
from tenacity import retry, stop_after_attempt, wait_fixed

PROMPT_TEMPLATE = """
# Context
{context}

# Code{filename}
```
{code}
```
-----
NOTICE
1. Role: You are a professional software engineer, and your main task is to review the code. You need to ensure that the code conforms to the PEP8 standards, is elegantly designed and modularized, easy to read and maintain, and is written in Python 3.9 (or in another programming language).
2. Task 1: Based on the following context and code, conduct a code review and provide improvement suggestions.
2. Task 2: Rewrite the code based on the improvement suggestions, ensure the code is complete and do not omit anything.
3. Check 0: Is the code implemented as per the requirements?
4. Check 1: Are there any issues with the code logic?
5. Check 2: Does the existing code follow the "data structure and interface definition"?
6. Check 3: Is the existing code complete and functional?
7. Check 4: Does the code have unnecessary dependencies?

## Code Review: Provide key, clear, concise, and specific code modification suggestions, up to 5.

## {filename}: Write code with triple quotes. Do your utmost to optimize THIS SINGLE FILE. ONLY USE EXISTING API. IF NO API, IMPLEMENT IT.
Ensure that the functionality of the rewritten code is consistent with the source code. 

"""


class WriteCodeReview(Action):
    def __init__(self, name="WriteCodeReview", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    async def write_code(self, prompt):
        code_rsp = await self._aask(prompt)
        code = CodeParser.parse_code(block="", text=code_rsp)
        return code

    async def run(self, context, code, filename):
        prompt = PROMPT_TEMPLATE.format(context=context, code=code, filename=filename)
        logger.info(f'Code review {filename}..')
        code = await self.write_code(prompt)
        # code_rsp = await self._aask_v1(prompt, "code_rsp", OUTPUT_MAPPING)
        # self._save(context, filename, code)
        return code
