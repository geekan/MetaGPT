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

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_random_exponential

from metagpt.actions.action import Action
from metagpt.actions.project_management_an import REFINED_TASK_LIST, TASK_LIST
from metagpt.actions.write_code_plan_and_change_an import REFINED_TEMPLATE
from metagpt.logs import logger
from metagpt.schema import CodingContext, Document, RunCodeResult
from metagpt.utils.common import CodeParser, get_markdown_code_block_type
from metagpt.utils.project_repo import ProjectRepo
from metagpt.utils.report import EditorReporter

PROMPT_TEMPLATE = """
NOTICE
Role: You are a professional engineer; the main goal is to write google-style, elegant, modular, easy to read and maintain code
Language: Please use the same language as the user requirement, but the title and code should be still in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

# Context
## Design
{design}

## Task
{task}

## Legacy Code
{code}

## Debug logs
```text
{logs}

{summary_log}
```

## Bug Feedback logs
```text
{feedback}
```

# Format example
## Code: {demo_filename}.py
```python
## {demo_filename}.py
...
```
## Code: {demo_filename}.js
```javascript
// {demo_filename}.js
...
```

# Instruction: Based on the context, follow "Format example", write code.

## Code: {filename}. Write code with triple quoto, based on the following attentions and context.
1. Only One file: do your best to implement THIS ONLY ONE FILE.
2. COMPLETE CODE: Your code will be part of the entire project, so please implement complete, reliable, reusable code snippets.
3. Set default value: If there is any setting, ALWAYS SET A DEFAULT VALUE, ALWAYS USE STRONG TYPE AND EXPLICIT VARIABLE. AVOID circular import.
4. Follow design: YOU MUST FOLLOW "Data structures and interfaces". DONT CHANGE ANY DESIGN. Do not use public member functions that do not exist in your design.
5. CAREFULLY CHECK THAT YOU DONT MISS ANY NECESSARY CLASS/FUNCTION IN THIS FILE.
6. Before using a external variable/module, make sure you import it first.
7. Write out EVERY CODE DETAIL, DON'T LEAVE TODO.

"""


class WriteCode(Action):
    name: str = "WriteCode"
    i_context: Document = Field(default_factory=Document)
    repo: Optional[ProjectRepo] = Field(default=None, exclude=True)
    input_args: Optional[BaseModel] = Field(default=None, exclude=True)

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
    async def write_code(self, prompt) -> str:
        code_rsp = await self._aask(prompt)
        code = CodeParser.parse_code(text=code_rsp)
        return code

    async def run(self, *args, **kwargs) -> CodingContext:
        bug_feedback = None
        if self.input_args and hasattr(self.input_args, "issue_filename"):
            bug_feedback = await Document.load(self.input_args.issue_filename)
        coding_context = CodingContext.loads(self.i_context.content)
        if not coding_context.code_plan_and_change_doc:
            coding_context.code_plan_and_change_doc = await self.repo.docs.code_plan_and_change.get(
                filename=coding_context.task_doc.filename
            )
        test_doc = await self.repo.test_outputs.get(filename="test_" + coding_context.filename + ".json")
        requirement_doc = await Document.load(self.input_args.requirements_filename)
        summary_doc = None
        if coding_context.design_doc and coding_context.design_doc.filename:
            summary_doc = await self.repo.docs.code_summary.get(filename=coding_context.design_doc.filename)
        logs = ""
        if test_doc:
            test_detail = RunCodeResult.loads(test_doc.content)
            logs = test_detail.stderr

        if self.config.inc or bug_feedback:
            code_context = await self.get_codes(
                coding_context.task_doc, exclude=self.i_context.filename, project_repo=self.repo, use_inc=True
            )
        else:
            code_context = await self.get_codes(
                coding_context.task_doc, exclude=self.i_context.filename, project_repo=self.repo
            )

        if self.config.inc:
            prompt = REFINED_TEMPLATE.format(
                user_requirement=requirement_doc.content if requirement_doc else "",
                code_plan_and_change=coding_context.code_plan_and_change_doc.content
                if coding_context.code_plan_and_change_doc
                else "",
                design=coding_context.design_doc.content if coding_context.design_doc else "",
                task=coding_context.task_doc.content if coding_context.task_doc else "",
                code=code_context,
                logs=logs,
                feedback=bug_feedback.content if bug_feedback else "",
                filename=self.i_context.filename,
                demo_filename=Path(self.i_context.filename).stem,
                summary_log=summary_doc.content if summary_doc else "",
            )
        else:
            prompt = PROMPT_TEMPLATE.format(
                design=coding_context.design_doc.content if coding_context.design_doc else "",
                task=coding_context.task_doc.content if coding_context.task_doc else "",
                code=code_context,
                logs=logs,
                feedback=bug_feedback.content if bug_feedback else "",
                filename=self.i_context.filename,
                demo_filename=Path(self.i_context.filename).stem,
                summary_log=summary_doc.content if summary_doc else "",
            )
        logger.info(f"Writing {coding_context.filename}..")
        async with EditorReporter(enable_llm_stream=True) as reporter:
            await reporter.async_report({"type": "code", "filename": coding_context.filename}, "meta")
            code = await self.write_code(prompt)
            if not coding_context.code_doc:
                # avoid root_path pydantic ValidationError if use WriteCode alone
                coding_context.code_doc = Document(
                    filename=coding_context.filename, root_path=str(self.repo.src_relative_path)
                )
            coding_context.code_doc.content = code
            await reporter.async_report(coding_context.code_doc, "document")
        return coding_context

    @staticmethod
    async def get_codes(task_doc: Document, exclude: str, project_repo: ProjectRepo, use_inc: bool = False) -> str:
        """
        Get codes for generating the exclude file in various scenarios.

        Attributes:
            task_doc (Document): Document object of the task file.
            exclude (str): The file to be generated. Specifies the filename to be excluded from the code snippets.
            project_repo (ProjectRepo): ProjectRepo object of the project.
            use_inc (bool): Indicates whether the scenario involves incremental development. Defaults to False.

        Returns:
            str: Codes for generating the exclude file.
        """
        if not task_doc:
            return ""
        if not task_doc.content:
            task_doc = project_repo.docs.task.get(filename=task_doc.filename)
        m = json.loads(task_doc.content)
        code_filenames = m.get(TASK_LIST.key, []) if not use_inc else m.get(REFINED_TASK_LIST.key, [])
        codes = []
        src_file_repo = project_repo.srcs
        # Incremental development scenario
        if use_inc:
            for filename in src_file_repo.all_files:
                code_block_type = get_markdown_code_block_type(filename)
                # Exclude the current file from the all code snippets
                if filename == exclude:
                    # If the file is in the old workspace, use the old code
                    # Exclude unnecessary code to maintain a clean and focused main.py file, ensuring only relevant and
                    # essential functionality is included for the project’s requirements
                    if filename != "main.py":
                        # Use old code
                        doc = await src_file_repo.get(filename=filename)
                    # If the file is in the src workspace, skip it
                    else:
                        continue
                    codes.insert(
                        0, f"### The name of file to rewrite: `{filename}`\n```{code_block_type}\n{doc.content}```\n"
                    )
                    logger.info(f"Prepare to rewrite `{filename}`")
                # The code snippets are generated from the src workspace
                else:
                    doc = await src_file_repo.get(filename=filename)
                    # If the file does not exist in the src workspace, skip it
                    if not doc:
                        continue
                    codes.append(f"### File Name: `{filename}`\n```{code_block_type}\n{doc.content}```\n\n")

        # Normal scenario
        else:
            for filename in code_filenames:
                # Exclude the current file to get the code snippets for generating the current file
                if filename == exclude:
                    continue
                doc = await src_file_repo.get(filename=filename)
                if not doc:
                    continue
                code_block_type = get_markdown_code_block_type(filename)
                codes.append(f"### File Name: `{filename}`\n```{code_block_type}\n{doc.content}```\n\n")

        return "\n".join(codes)
