#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:12
@Author  : alexanderwu
@File    : project_management.py
@Modified By: mashenquan, 2023/11/27.
        1. Divide the context into three components: legacy code, unit test code, and console log.
        2. Move the document storage operations related to WritePRD from the save operation of WriteDesign.
        3. According to the design in Section 2.2.3.5.4 of RFC 135, add incremental iteration functionality.
"""
import json
from typing import List

from metagpt.actions import ActionOutput
from metagpt.actions.action import Action
from metagpt.config import CONFIG
from metagpt.const import (
    PACKAGE_REQUIREMENTS_FILENAME,
    SYSTEM_DESIGN_FILE_REPO,
    TASK_FILE_REPO,
    TASK_PDF_FILE_REPO,
)
from metagpt.logs import logger
from metagpt.schema import Document, Documents
from metagpt.utils.file_repository import FileRepository
from metagpt.utils.get_template import get_template

templates = {
    "json": {
        "PROMPT_TEMPLATE": """
# Context
{context}

## Format example
{format_example}
-----
Role: You are a project manager; the goal is to break down tasks according to PRD/technical design, give a task list, and analyze task dependencies to start with the prerequisite modules
Language: Please use the same language as the user requirement, but the title and code should be still in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
Requirements: Based on the context, fill in the following missing information, each section name is a key in json. Here the granularity of the task is a file, if there are any missing files, you can supplement them
ATTENTION: Output carefully referenced "Format example" in format.

## Required Python third-party packages: Provide Python list[str] in requirements.txt format

## Required Other language third-party packages: Provide Python list[str] in requirements.txt format

## Logic Analysis: Provided as a Python list[list[str]. the first is filename, the second is class/method/function should be implemented in this file. Analyze the dependencies between the files, which work should be done first

## Task list: Provided as Python list[str]. Each str is a filename, the more at the beginning, the more it is a prerequisite dependency, should be done first

## Full API spec: Use OpenAPI 3.0. Describe all APIs that may be used by both frontend and backend.

## Shared Knowledge: Anything that should be public like utils' functions, config's variables details that should make clear first. 

## Anything UNCLEAR: Provide as Plain text. Try to clarify it. For example, don't forget a main entry. don't forget to init 3rd party libs.

output a properly formatted JSON, wrapped inside [CONTENT][/CONTENT] like format example,
and only output the json inside this tag, nothing else
""",
        "FORMAT_EXAMPLE": '''
{
    "Required Python third-party packages": [
        "flask==1.1.2",
        "bcrypt==3.2.0"
    ],
    "Required Other language third-party packages": [
        "No third-party ..."
    ],
    "Logic Analysis": [
        ["game.py", "Contains..."]
    ],
    "Task list": [
        "game.py"
    ],
    "Full API spec": """
        openapi: 3.0.0
        ...
        description: A JSON object ...
     """,
    "Shared Knowledge": """
        'game.py' contains ...
    """,
    "Anything UNCLEAR": "We need ... how to start."
}
''',
    },
    "markdown": {
        "PROMPT_TEMPLATE": """
# Context
{context}

## Format example
{format_example}
-----
Role: You are a project manager; the goal is to break down tasks according to PRD/technical design, give a task list, and analyze task dependencies to start with the prerequisite modules
Requirements: Based on the context, fill in the following missing information, note that all sections are returned in Python code triple quote form seperatedly. Here the granularity of the task is a file, if there are any missing files, you can supplement them
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote.

## Required Python third-party packages: Provided in requirements.txt format

## Required Other language third-party packages: Provided in requirements.txt format

## Logic Analysis: Provided as a Python list[list[str]. the first is filename, the second is class/method/function should be implemented in this file. Analyze the dependencies between the files, which work should be done first

## Task list: Provided as Python list[str]. Each str is a filename, the more at the beginning, the more it is a prerequisite dependency, should be done first

## Full API spec: Use OpenAPI 3.0. Describe all APIs that may be used by both frontend and backend.

## Shared Knowledge: Anything that should be public like utils' functions, config's variables details that should make clear first. 

## Anything UNCLEAR: Provide as Plain text. Try to clarify it. For example, don't forget a main entry. don't forget to init 3rd party libs.

""",
        "FORMAT_EXAMPLE": '''
---
## Required Python third-party packages
```python
"""
flask==1.1.2
bcrypt==3.2.0
"""
```

## Required Other language third-party packages
```python
"""
No third-party ...
"""
```

## Full API spec
```python
"""
openapi: 3.0.0
...
description: A JSON object ...
"""
```

## Logic Analysis
```python
[
    ["index.js", "Contains ..."],
    ["main.py", "Contains ..."],
]
```

## Task list
```python
[
    "index.js",
    "main.py",
]
```

## Shared Knowledge
```python
"""
'game.py' contains ...
"""
```

## Anything UNCLEAR
We need ... how to start.
---
''',
    },
}
OUTPUT_MAPPING = {
    "Required Python third-party packages": (List[str], ...),
    "Required Other language third-party packages": (List[str], ...),
    "Full API spec": (str, ...),
    "Logic Analysis": (List[List[str]], ...),
    "Task list": (List[str], ...),
    "Shared Knowledge": (str, ...),
    "Anything UNCLEAR": (str, ...),
}

MERGE_PROMPT = """
# Context
{context}

## Old Tasks
{old_tasks}
-----

## Format example
{format_example}
-----
Role: You are a project manager; The goal is to merge the new PRD/technical design content from 'Context' into 'Old Tasks.' Based on this merged result, break down tasks, give a task list, and analyze task dependencies to start with the prerequisite modules.
Requirements: Based on the context, fill in the following missing information, each section name is a key in json. Here the granularity of the task is a file, if there are any missing files, you can supplement them
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote.

## Required Python third-party packages: Provided in requirements.txt format

## Required Other language third-party packages: Provided in requirements.txt format

## Full API spec: Use OpenAPI 3.0. Describe all APIs that may be used by both frontend and backend.

## Logic Analysis: Provided as a Python list[list[str]. the first is filename, the second is class/method/function should be implemented in this file. Analyze the dependencies between the files, which work should be done first

## Task list: Provided as Python list[str]. Each str is a filename, the more at the beginning, the more it is a prerequisite dependency, should be done first

## Shared Knowledge: Anything that should be public like utils' functions, config's variables details that should make clear first. 

## Anything UNCLEAR: Provide as Plain text. Make clear here. For example, don't forget a main entry. don't forget to init 3rd party libs.

output a properly formatted JSON, wrapped inside [CONTENT][/CONTENT] like "Format example" format,
and only output the json inside this tag, nothing else
"""


class WriteTasks(Action):
    def __init__(self, name="CreateTasks", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, with_messages, format=CONFIG.prompt_format):
        system_design_file_repo = CONFIG.git_repo.new_file_repository(SYSTEM_DESIGN_FILE_REPO)
        changed_system_designs = system_design_file_repo.changed_files

        tasks_file_repo = CONFIG.git_repo.new_file_repository(TASK_FILE_REPO)
        changed_tasks = tasks_file_repo.changed_files
        change_files = Documents()
        # Rewrite the system designs that have undergone changes based on the git head diff under
        # `docs/system_designs/`.
        for filename in changed_system_designs:
            task_doc = await self._update_tasks(
                filename=filename, system_design_file_repo=system_design_file_repo, tasks_file_repo=tasks_file_repo
            )
            change_files.docs[filename] = task_doc

        # Rewrite the task files that have undergone changes based on the git head diff under `docs/tasks/`.
        for filename in changed_tasks:
            if filename in change_files.docs:
                continue
            task_doc = await self._update_tasks(
                filename=filename, system_design_file_repo=system_design_file_repo, tasks_file_repo=tasks_file_repo
            )
            change_files.docs[filename] = task_doc

        if not change_files.docs:
            logger.info("Nothing has changed.")
        # Wait until all files under `docs/tasks/` are processed before sending the publish_message, leaving room for
        # global optimization in subsequent steps.
        return ActionOutput(content=change_files.json(), instruct_content=change_files)

    async def _update_tasks(self, filename, system_design_file_repo, tasks_file_repo):
        system_design_doc = await system_design_file_repo.get(filename)
        task_doc = await tasks_file_repo.get(filename)
        if task_doc:
            task_doc = await self._merge(system_design_doc=system_design_doc, task_doc=task_doc)
        else:
            rsp = await self._run_new_tasks(context=system_design_doc.content)
            task_doc = Document(
                root_path=TASK_FILE_REPO, filename=filename, content=rsp.instruct_content.json(ensure_ascii=False)
            )
        await tasks_file_repo.save(
            filename=filename, content=task_doc.content, dependencies={system_design_doc.root_relative_path}
        )
        await self._update_requirements(task_doc)
        await self._save_pdf(task_doc=task_doc)
        return task_doc

    async def _run_new_tasks(self, context, format=CONFIG.prompt_format):
        prompt_template, format_example = get_template(templates, format)
        prompt = prompt_template.format(context=context, format_example=format_example)
        rsp = await self._aask_v1(prompt, "task", OUTPUT_MAPPING, format=format)
        return rsp

    async def _merge(self, system_design_doc, task_doc, format=CONFIG.prompt_format) -> Document:
        _, format_example = get_template(templates, format)
        prompt = MERGE_PROMPT.format(context=system_design_doc.content, old_tasks=task_doc.content,
                                     format_example=format_example)
        rsp = await self._aask_v1(prompt, "task", OUTPUT_MAPPING, format=format)
        task_doc.content = rsp.instruct_content.json(ensure_ascii=False)
        return task_doc

    @staticmethod
    async def _update_requirements(doc):
        m = json.loads(doc.content)
        packages = set(m.get("Required Python third-party packages", set()))
        file_repo = CONFIG.git_repo.new_file_repository()
        requirement_doc = await file_repo.get(filename=PACKAGE_REQUIREMENTS_FILENAME)
        if not requirement_doc:
            requirement_doc = Document(filename=PACKAGE_REQUIREMENTS_FILENAME, root_path=".", content="")
        lines = requirement_doc.content.splitlines()
        for pkg in lines:
            if pkg == "":
                continue
            packages.add(pkg)
        await file_repo.save(PACKAGE_REQUIREMENTS_FILENAME, content="\n".join(packages))

    @staticmethod
    async def _save_pdf(task_doc):
        await FileRepository.save_as(doc=task_doc, with_suffix=".md", relative_path=TASK_PDF_FILE_REPO)


class AssignTasks(Action):
    async def run(self, *args, **kwargs):
        # Here you should implement the actual action
        pass
