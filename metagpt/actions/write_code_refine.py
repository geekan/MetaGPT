#!/usr/bin/env python
# -*- coding: utf-8 -*-

from metagpt.actions.action import Action
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.utils.common import CodeParser
from tenacity import retry, stop_after_attempt, wait_fixed

PROMPT_TEMPLATE = """
NOTICE
Role: You are a professional engineer; your primary goal is to write PEP8 compliant, elegant, modular, easy-to-read, and maintainable Python 3.9 code (or any other programming language of your choice). 
Requirements: You should modify the corresponding code based on the guidance. Then, output the complete code, fixing all errors according to the context. Ensure that you adhere to the specified guidelines for incremental development and modification of legacy code. 
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format should be carefully referenced using the "Format example". Only output the current modified code, nothing else. In the modified code, if unchanged, you should output it, the complete code.

## Code: Only Write {filename}, Write code using triple quotes, based on the following list and context.
1. Do your best to implement THIS ONLY ONE FILE. ONLY USE EXISTING API. IF NO API, IMPLEMENT IT.
2. Requirement: Implement one of the following code files based on the provided context. Return the code in the specified format. Your code will be part of the entire project, so ensure it is complete, reliable, and reusable.
3. Attention1: If there is any setting, ALWAYS SET A DEFAULT VALUE, ALWAYS USE STRONG TYPE AND EXPLICIT VARIABLE.
4. Attention2: YOU MUST FOLLOW "Data structures and interface definitions". DONT CHANGE ANY DESIGN.
5. Think before writing: What should be implemented and provided in this document?
6. CAREFULLY CHECK THAT YOU DONT MISS ANY NECESSARY CLASS/FUNCTION IN THIS FILE.
7. Do not use public member functions that do not exist in your design.
-----
# Context
{context}

-----
## Guidelines: The foremost guidelines of modification for incremental development.
{guide}

-----
## Legacy Code: The Legacy Code that needs to be modified.
{legacy}

-----
## Format example
-----
## Modified/Added Code: {filename}
```python
# {filename}
...
```
-----
"""


class WriteCodeRefine(Action):
    def __init__(self, name="WriteCodeRefine", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    async def write_code(self, prompt):
        code_rsp = await self._aask(prompt)
        code = CodeParser.parse_code(block="", text=code_rsp)
        return code

    async def run(self, context, code, filename, guide):
        prompt = PROMPT_TEMPLATE.format(context=context, legacy=code, filename=filename, guide=guide)
        logger.info(f'Code refine {filename}..')
        code = await self.write_code(prompt)
        # code_rsp = await self._aask_v1(prompt, "code_rsp", OUTPUT_MAPPING)
        # self._save(context, filename, code)
        return code
    