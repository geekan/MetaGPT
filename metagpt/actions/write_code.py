#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : write_code.py
"""
from metagpt.actions import WriteDesign
from metagpt.actions.action import Action
from metagpt.const import WORKSPACE_ROOT
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.utils.common import CodeParser

PROMPT_TEMPLATE = """
# Context
{context}
-----
NOTICE
1. Role: You are an engineer; the main goal is to write PEP8 compliant, elegant, modular, easy to read and maintain Python 3.9 code (but you can also use other programming language)
2. Requirement: Based on the context, implement one following code file, note to return only in code form, your code will be part of the entire project, so please implement complete, reliable, reusable code snippets
3. Attention1: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the code.
4. Attention2: If there is any setting, ALWAYS SET A DEFAULT VALUE, ALWAYS USE STRONG TYPE AND EXPLICIT VARIABLE.
5. Attention3: YOU MUST FOLLOW "Data structures and interface definitions". DONT CHANGE ANY DESIGN.
6. Think before writing: What should be implemented and provided in this document?
7. CAREFULLY CHECK THAT YOU DONT MISS ANY NECESSARY CLASS/FUNCTION IN THIS FILE.
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote.

## {filename}: Write code with triple quoto. Do your best to implement THIS ONLY ONE FILE. ONLY USE EXISTING API. IF NO API, IMPLEMENT IT.

"""

## {filename}: Please encapsulate your code within triple quotes. Focus your efforts on implementing ONLY WITHIN THIS FILE. Any class or function labeled as MISSING-DESIGN should be implemented IN THIS FILE ALONE. Do NOT make changes to any other files.
OUTPUT_MAPPING = {
    "{filename}": (str, ...),
}


class WriteCode(Action):
    def __init__(self, name="WriteCode", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)

    def _is_invalid(self, filename):
        return any(i in filename for i in ["mp3", "wav"])

    def _save(self, context, filename, code_rsp):
        # logger.info(filename)
        # logger.info(code_rsp)
        if self._is_invalid(filename):
            return

        design = [i for i in context if i.cause_by == WriteDesign][0]

        ws_name = CodeParser.parse_str(block="Python package name", text=design.content)
        ws_path = WORKSPACE_ROOT / ws_name
        if f"{ws_name}/" not in filename and all(i not in filename for i in ["requirements.txt", ".md"]):
            ws_path = ws_path / ws_name
        code_path = ws_path / filename
        code_path.parent.mkdir(parents=True, exist_ok=True)
        code = CodeParser.parse_code(block="", text=code_rsp)
        code_path.write_text(code)
        logger.info(f"Saving Code to {code_path}")

    async def run(self, **kwargs):
        prompt = PROMPT_TEMPLATE.format(**kwargs)
        filename = kwargs['filename']
        context = kwargs['context']
        logger.info(f'Writing {filename}..')
        code_rsp = await self._aask(prompt)
        # code_rsp = await self._aask_v1(prompt, "code_rsp", OUTPUT_MAPPING)
        self._save(context, filename, code_rsp)
        return code_rsp
