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
NOTICE
Role: You are a professional software engineer, and your main task is to review the code. You need to ensure that the code conforms to the PEP8 standards, is elegantly designed and modularized, easy to read and maintain, and is written in Python 3.9 (or in another programming language).
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

## Code Review: Based on the following context and code, follow the check list, Provide key, clear, concise, and specific code modification suggestions, up to 5.
1. Is the code implemented as per the requirements? If not, how to achieve it? Analyse it step by step.
2. Are there any issues with the code logic? If so, how to solve it?
3. Does the existing code follow the "Data structures and interfaces"?
4. Is there a function in the code that is not fully implemented? If so, how to implement it?
5. Does the code have unnecessary or lack dependencies? If so, how to solve it?

## Rewrite Code: rewrite {filename} based on "Code Review" with triple quotes. Do your utmost to optimize THIS SINGLE FILE. Implement ALL TODO.
-----
# Context
{context}

## Code: {filename}
```
{code}
```
-----

## Format example
-----
{format_example}
-----

"""

FORMAT_EXAMPLE = """

## Code Review
1. No, we should add the logic of ...
2. ...
3. ...
4. ...
5. ...

## Rewrite Code: {filename}
```python
## {filename}
...
```
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
        format_example = FORMAT_EXAMPLE.format(filename=filename)
        prompt = PROMPT_TEMPLATE.format(context=context, code=code, filename=filename, format_example=format_example)
        logger.info(f'Code review {filename}..')
        code = await self.write_code(prompt)
        # code_rsp = await self._aask_v1(prompt, "code_rsp", OUTPUT_MAPPING)
        # self._save(context, filename, code)
        return code
    