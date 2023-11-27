#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : write_code.py
@Modified By: mashenquan, 2023-11-1. In accordance with Chapter 2.1.3 of RFC 116, modify the data type of the `cause_by`
            value of the `Message` object.
@Modified By: mashenquan, 2023-11-27.
        1. Mark the location of Design, Tasks, Legacy Code and Debug logs in the PROMPT_TEMPLATE with markdown
        code-block formatting to enhance the understanding for the LLM.
        2. Following the think-act principle, solidify the task parameters when creating the WriteCode object, rather
        than passing them in when calling the run function.
        3. Encapsulate the input of RunCode into RunCodeContext and encapsulate the output of RunCode into
        RunCodeResult to standardize and unify parameter passing between WriteCode, RunCode, and DebugError.
"""

from tenacity import retry, stop_after_attempt, wait_fixed

from metagpt.actions.action import Action
from metagpt.config import CONFIG
from metagpt.const import TEST_OUTPUTS_FILE_REPO
from metagpt.logs import logger
from metagpt.schema import CodingContext, RunCodeResult
from metagpt.utils.common import CodeParser

PROMPT_TEMPLATE = """
NOTICE
Role: You are a professional engineer; the main goal is to write PEP8 compliant, elegant, modular, easy to read and maintain Python 3.9 code (but you can also use other programming language)
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

## Code: {filename} Write code with triple quoto, based on the following list and context.
1. Do your best to implement THIS ONLY ONE FILE. ONLY USE EXISTING API. IF NO API, IMPLEMENT IT.
2. Requirement: Based on the context, implement one following code file, note to return only in code form, your code will be part of the entire project, so please implement complete, reliable, reusable code snippets
3. Attention1: If there is any setting, ALWAYS SET A DEFAULT VALUE, ALWAYS USE STRONG TYPE AND EXPLICIT VARIABLE.
4. Attention2: YOU MUST FOLLOW "Data structures and interface definitions". DONT CHANGE ANY DESIGN.
5. Think before writing: What should be implemented and provided in this document?
6. CAREFULLY CHECK THAT YOU DONT MISS ANY NECESSARY CLASS/FUNCTION IN THIS FILE.
7. Do not use public member functions that do not exist in your design.

-----
# Design
```json
{design}
```
-----
# Tasks
```json
{tasks}
```
-----
# Legacy Code
```python
{code}
```
-----
# Debug logs
```text
{logs}
```
-----
## Format example
-----
## Code: {filename}
```python
## {filename}
...
```
-----
"""


class WriteCode(Action):
    def __init__(self, name="WriteCode", context=None, llm=None):
        super().__init__(name, context, llm)

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    async def write_code(self, prompt) -> str:
        code_rsp = await self._aask(prompt)
        code = CodeParser.parse_code(block="", text=code_rsp)
        return code

    async def run(self, *args, **kwargs) -> CodingContext:
        coding_context = CodingContext.loads(self.context.content)
        test_doc = await CONFIG.git_repo.new_file_repository(TEST_OUTPUTS_FILE_REPO).get(
            "test_" + coding_context.filename + ".json"
        )
        logs = ""
        if test_doc:
            test_detail = RunCodeResult.loads(test_doc.content)
            logs = test_detail.stderr
        prompt = PROMPT_TEMPLATE.format(
            design=coding_context.design_doc.content,
            tasks=coding_context.task_doc.content,
            code=coding_context.code_doc.content,
            logs=logs,
            filename=self.context.filename,
        )
        logger.info(f"Writing {coding_context.filename}..")
        code = await self.write_code(prompt)
        coding_context.code_doc.content = code
        return coding_context
