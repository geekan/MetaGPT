#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import List, Union

from metagpt.actions.action import Action
from metagpt.config import CONFIG
from metagpt.const import WORKSPACE_ROOT
from metagpt.utils.common import CodeParser
from metagpt.utils.get_template import get_template
from metagpt.utils.json_to_markdown import json_to_markdown

templates = {
    "json": {
        "PROMPT_TEMPLATE": """
# Context
{context}

## Legacy
{legacy}

## Format example
{format_example}
-----
Role: You are a project manager; the goal is to perform incremental development based on the context and the legacy. Break down tasks according to PRD/technical design, provide a Task list, and analyze task dependencies to start with the prerequisite modules.
Requirements: Based on the context and the Legacy Project Management and Legacy Code, fill in the following missing information. Note that Please try your best to reuse legacy code, and all sections are returned in Python code triple quote form seperatedly. Here the granularity of the task is a file that need to modified.
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote.
Output a properly formatted JSON, wrapped inside [CONTENT][/CONTENT]. The following is the attribute description of the JSON object.

## Required Python third-party packages: Provided as a python list, the requirements.txt format

## Full API spec: Use OpenAPI 3.0. Describe all APIs that may be used by both frontend and backend based on the previous.

## Task list: Provided as Python list[str]. Each str is a filename, the more at the beginning, the more it is a prerequisite dependency, should be done first. 

Output a properly formatted JSON, wrapped inside [CONTENT][/CONTENT] like format example,
and only output the json inside this tag, nothing else
""",
        "FORMAT_EXAMPLE": '''
{
    "Required Python third-party packages": [
        "flask==1.1.2",
        "bcrypt==3.2.0"
    ],
    "Full API spec": """
        openapi: 3.0.0
        ...
        description: A JSON object ...
     """,
    "Task list": [
        "game.py"
    ]
}
''',
    },
    "markdown": {
        "PROMPT_TEMPLATE": """
# Context
{context}

## Legacy
{legacy}

## Format example
{format_example}
-----
Role: You are a project manager; the goal is to perform incremental development based on the context and the legacy. Break down tasks according to PRD/technical design, provide a Task list need to modified files, and analyze task dependencies to start with the prerequisite modules.
Requirements: Based on the context and the Legacy Project Management and Legacy Code, fill in the following missing information. Note that Please try your best to reuse legacy code, and all sections are returned in Python code triple quote form seperatedly. Here the granularity of the task is a file that need to modified.
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote.

## Required Python third-party packages: Provided as a python list, the requirements.txt format

## Full API spec: Use OpenAPI 3.0. Describe all APIs that may be used by both frontend and backend based on the previous.

## Task list: Provided as Python list[str]. Each str is a filename, the more at the beginning, the more it is a prerequisite dependency, should be done first. 
""",
        "FORMAT_EXAMPLE": '''
---

## Required Python third-party packages
```python
[
    "flask==1.1.2",
    "bcrypt==3.2.0"
]
```

## Full API spec
```python
"""
openapi: 3.0.0
...
description: A JSON object ...
"""
```

## Task list
```python
[
    "game.py",
]
```
---
''',
    },
}
OUTPUT_MAPPING = {
    # "Incremental Requirements": (str, ...),
    # ## Incremental Requirements: Provided as a str, the foremost incremental requirements for project management here based on the previous.
    # "Difference Analysis": (Union[List[str], str], ...),
    "Required Python third-party packages": (Union[List[str], str], ...),
    "Full API spec": (str, ...),
    # "Logic Analysis": (List[List[str]], ...),
    "Task list": (List[str], ...),
}


class RefineTasks(Action):
    def __init__(self, name="RefineTasks", context=None, llm=None):
        super().__init__(name, context, llm)

    def _save(self, context, rsp):
        if context[-1].instruct_content:
            ws_name = context[-1].instruct_content.dict()["Python package name"]
        else:
            ws_name = CodeParser.parse_str(block="Python package name", text=context[-1].content)
        file_path = WORKSPACE_ROOT / ws_name / "docs/api_spec_and_tasks.md"
        file_path.write_text(json_to_markdown(rsp.instruct_content.dict()))

        # Write requirements.txt
        requirements_path = WORKSPACE_ROOT / ws_name / "requirements.txt"
        requirements_path.write_text("\n".join(rsp.instruct_content.dict().get("Required Python third-party packages")))

    async def run(self, context, legacy, format=CONFIG.prompt_format):
        prompt_template, format_example = get_template(templates, format)
        prompt = prompt_template.format(context=context,
                                        legacy=legacy,
                                        format_example=format_example)
        rsp = await self._aask_v1(prompt, "task", OUTPUT_MAPPING, format=format)
        self._save(context, rsp)
        return rsp


class AssignTasks(Action):
    async def run(self, *args, **kwargs):
        # Here you should implement the actual action
        pass
