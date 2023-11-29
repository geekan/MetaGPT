#!/usr/bin/env python
# -*- coding: utf-8 -*-

from metagpt.actions.action import Action
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.utils.common import CodeParser
from tenacity import retry, stop_after_attempt, wait_fixed


PROMPT_TEMPLATE = """
NOTICE
Role: You are a professional software engineer, and your main task is to conduct incremental development, proposing incremental development plans and code guideance based on context and legacy code. Existing code and logic that need to be retained must also appear in the code after incremental development, do not omit it. Ensure that the code conforms to the PEP8 standards, is elegantly designed and modularized, easy to read and maintain, and is written in Python 3.9 (or in another programming language).
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

## Regulations Review: To make the software directly operable without further coding, follow the regulations below during incremental development:
1) Import all referenced classes.
2) Implement all methods.
3) Add necessary explanation to all methods.
4) Ensure there are no potential bugs.
5) Confirm that the entire project conforms to the tasks proposed by the user.
6) Review the code thoroughly, checking for errors and validating the logic to ensure seamless user interaction without compromising any specified requirements.

## Incremental Development Plan: Proposed the Minimum essential incremental development plan, based on the following context and legacy code by thinking step by step. 
...

## Code guidelines: Propose the foremost guidelines that how to implement code of modification part for incremental development based on the above context, legacy code and incremental development plan.
```python
...
'''
-----
# Context
{context}

## Legacy Code
You are tasked with conducting incremental development in the existing code based on the provided legacy code and above information.
```
{code}
```
-----

## Format example
-----
## Incremental Development Guide: 
...

## Code Guidance:
# Implementation the ...
```python
...
'''
-----
"""


class WriteCodeGuide(Action):
    def __init__(self, name="WriteCodeGuide", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context, code):
        prompt = PROMPT_TEMPLATE.format(context=context, code=code)
        logger.info(f'Write Code Guide ..')
        code_guide = await self._aask(prompt)
        # code_rsp = await self._aask_v1(prompt, "code_rsp", OUTPUT_MAPPING)
        # self._save(context, filename, code)
        return code_guide
    