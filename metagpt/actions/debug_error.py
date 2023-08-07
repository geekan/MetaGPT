#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:46
@Author  : alexanderwu
@File    : debug_error.py
"""
import re

from metagpt.logs import logger
from metagpt.actions.action import Action
from metagpt.utils.common import CodeParser

PROMPT_TEMPLATE = """
NOTICE
1. Role: You are a Development Engineer or QA engineer;
2. Task: You received this message from another Development Engineer or QA engineer who ran or tested your code. 
Based on the message, first, figure out your own role, i.e. Engineer or QaEngineer,
then rewrite the development code or the test code based on your role, the error, and the summary, such that all bugs are fixed and the code performs well.
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the test case or script and triple quotes.
The message is as follows:
{context}
---
Now you should start rewriting the code:
## file name of the code to rewrite: Write code with triple quoto. Do your best to implement THIS IN ONLY ONE FILE.
"""
class DebugError(Action):
    def __init__(self, name="DebugError", context=None, llm=None):
        super().__init__(name, context, llm)

    # async def run(self, code, error):
    #     prompt = f"Here is a piece of Python code:\n\n{code}\n\nThe following error occurred during execution:" \
    #              f"\n\n{error}\n\nPlease try to fix the error in this code."
    #     fixed_code = await self._aask(prompt)
    #     return fixed_code
    
    async def run(self, context):
        if "PASS" in context:
            return "", "the original code works fine, no need to debug"
        
        file_name = re.search("## File To Rewrite:\s*(.+\\.py)", context).group(1)

        logger.info(f"Debug and rewrite {file_name}")

        prompt = PROMPT_TEMPLATE.format(context=context)
        
        rsp = await self._aask(prompt)

        code = CodeParser.parse_code(block="", text=rsp)

        return file_name, code
