#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:12
@Author  : alexanderwu
@File    : project_management.py
"""

from metagpt.actions.action import Action
from metagpt.const import WORKSPACE_ROOT
from metagpt.logs import logger
from metagpt.utils.common import CodeParser

PROMPT_TEMPLATE = """
# Context
{context}
-----
Role: You are a project manager; the goal is to break down tasks according to PRD/technical design, give a task list, and analyze task dependencies to start with the prerequisite modules
Requirements: Based on the context, fill in the following missing information, note that all sections are returned in Python code triple quote form seperatedly. Here the granularity of the task is a file, if there are any missing files, you can supplement them
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote.

## Required Python third-party packages: Provided in requirements.txt format

## Required Other language third-party packages: Provided in requirements.txt format

## Full API spec: Use OpenAPI 3.0. Describe all APIs that may be used by both frontend and backend.

## Logic Analysis: Provided as a Python list[str, str]. the first is filename, the second is class/method/function should be implemented in this file. Analyze the dependencies between the files, which work should be done first

## Task list: Provided as Python list[str]. Each str is a filename, the more at the beginning, the more it is a prerequisite dependency, should be done first

## Shared Knowledge: Anything that should be public like utils' functions, config's variables details that should make clear first. 

## Anything UNCLEAR: Provide as Plain text. Make clear here. For example, don't forget a main entry. don't forget to init 3rd party libs.

"""


class WriteTasks(Action):
    def __init__(self, name="CreateTasks", context=None, llm=None):
        super().__init__(name, context, llm)

    def _save(self, context, rsp):
        ws_name = CodeParser.parse_str(block="Python package name", text=context[-1].content)
        file_path = WORKSPACE_ROOT / ws_name / 'docs/api_spec_and_tasks.md'
        file_path.write_text(rsp)

    async def run(self, context):
        prompt = PROMPT_TEMPLATE.format(context=context)
        rsp = await self._aask(prompt)
        self._save(context, rsp)
        return rsp


class AssignTasks(Action):
    async def run(self, *args, **kwargs):
        # Here you should implement the actual action
        pass
