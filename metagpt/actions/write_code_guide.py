#!/usr/bin/env python
# -*- coding: utf-8 -*-

from metagpt.actions.action import Action
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.utils.common import CodeParser
from tenacity import retry, stop_after_attempt, wait_fixed


PROMPT_TEMPLATE = """
NOTICE
Role: You are a professional software engineer, and your main task is to conduct incremental development, proposing incremental development plans and code guideance based on context and legacy code. Existing code and logic that need to be retained must also appear in the code after incremental development, do not omit it. Ensure that the code conforms to the PEP8 standards, is elegantly designed and modularized, easy to read and maintain, and is written in Python 3.9 (or in another programming language). Output format carefully referenced "Format example".

## Regulations Review: To make the software directly operable without further coding, follow the regulations below during incremental development:
0) Determine the scope of responsibilities of each file and what classes and methods need to be implemented.
1) Import all referenced classes.
2) Implement all methods. 
3) Add necessary explanation to all methods. 
4) Ensure there are no potential bugs.
5) Confirm that the entire project conforms to the tasks proposed by the user.
6) Review the code thoroughly, checking for errors and validating the logic to ensure seamless user interaction without compromising any specified requirements.

## Incremental Development Plan: Provided as a Python list containing `filename.py`. Proposed the detail and essential incremental development plan, based on the following context and legacy code by thinking and analyzing step by step. All incremental modules/functions need to be added to the corresponding code files.

## Code Guidance: Propose the foremost guidelines that how to implement code of modification part for incremental development based on the above context, legacy code and incremental development plan.

-----
# Context
{context}

## Legacy Code
You are tasked with conducting incremental development in the existing code based on the provided legacy code and above information.
```
{legacy}
```
-----

## Format example
-----
## Incremental Development Guide
[
    "`game.py` Contains `Game` and ...",
]


## Code Guidance
### Implementation `xx` in `xxx.py` ..., else retain the original xxx.py code.
```python
## xxx.py
...
```
---
### Implementation of the `Game` in `game.py` ..., else retain the original game.py code.
```python
## game.py
class Game:
    ...
```
-----
"""


class WriteCodeGuide(Action):
    def __init__(self, name="WriteCodeGuide", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, context, legacy):
        prompt = PROMPT_TEMPLATE.format(context=context, legacy=legacy)
        logger.info(f'Write Code Guide ..')
        code_guide = await self._aask(prompt)
        # code_rsp = await self._aask_v1(prompt, "code_rsp", OUTPUT_MAPPING)
        return code_guide
    