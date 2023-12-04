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
Requirements: Rewrite the complete code based on the Legacy Code so that it can be executed and avoid any potential bugs. You should modify the corresponding code based on the guidance. Output the complete code, fixing all errors according to the context. Ensure that you adhere to the specified guidelines for incremental development and modification of legacy code.
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format should be carefully referenced using the "Format example". Only output the current modified code, nothing else. In the modified code, if unchanged, you should output it, the complete code.

## Rewrite Complete Code: Only Write one file {filename}, Write code using triple quotes, based on the following list, context, guidelines and legacy code.
1. Important: Do your best to implement ONLY ONE FILE. ONLY USE EXISTING API. IF NO API, IMPLEMENT IT.
2. Implement one of the following code files based on the provided context. Return the code in the specified format. Your code will be part of the entire project, so ensure it is complete, reliable, and reusable. 
3. Attention1: Implement the functions required by the current file scope of responsibility. For example, main only needs to focus on the basic functions of main.py in the legacy code and the incremental functions to be implemented. Reuse existing code as much as possible. You can import functions from other codes instead of reimplementing the function. If there is any setting, ALWAYS SET A DEFAULT VALUE, ALWAYS USE STRONG TYPE AND EXPLICIT VARIABLE.
4. Attention2: Make modifications and additions to the legacy code in accordance with the provided guidelines and API. Ensure that the complete code is implemented without any omissions, taking into account the guidelines, context, and existing legacy code. Retain the basic function methods from the legacy code, and make sure to preserve the existing code and logic that needs to be retained throughout the incremental development process. Avoid omitting any essential components. 
5. Think before writing: What should be implemented and provided in this document?
6. CAREFULLY CHECK THAT YOU DONT MISS ANY NECESSARY CLASS/FUNCTION IN THIS FILE.
7. Do not use public member functions that do not exist in your design.
8. The Modified Code is implemented according to the requirements, and there are no issues with the code logic. All functions in the Modified Code are fully implemented; none are omitted or incomplete.

-----
# Context
{context}

-----
## Guidelines: The foremost guidelines of modification for incremental development.
{guide}

-----
## Legacy Code: The Legacy Code that needs to be modified. '===' is the separator of each code file in the legacy code. Basic function methods need to be retained in {filename}.
{legacy}

-----
## Format example
-----
## Rewrite Complete Code: {filename}
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

    async def run(self, context, legacy, filename, guide):
        prompt = PROMPT_TEMPLATE.format(context=context, legacy=legacy, filename=filename, guide=guide)
        logger.info(f'Code refine {filename}..')
        code = await self.write_code(prompt)
        # code_rsp = await self._aask_v1(prompt, "code_rsp", OUTPUT_MAPPING)
        # self._save(context, filename, code)
        return code
    