#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : write_code_review.py
@Modified By: mashenquan, 2023/11/27. Following the think-act principle, solidify the task parameters when creating the
        WriteCode object, rather than passing them in when calling the run function.
"""
import asyncio
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_random_exponential

from metagpt.actions import WriteCode
from metagpt.actions.action import Action
from metagpt.logs import logger
from metagpt.schema import CodingContext, Document
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import CodeParser, aread, awrite
from metagpt.utils.project_repo import ProjectRepo
from metagpt.utils.report import EditorReporter

PROMPT_TEMPLATE = """
# System
Role: You are a professional software engineer, and your main task is to review and revise the code. You need to ensure that the code conforms to the google-style standards, is elegantly designed and modularized, easy to read and maintain.
Language: Please use the same language as the user requirement, but the title and code should be still in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

# Context
{context}

-----

## Code to be Reviewed: {filename}
```Code
{code}
```
"""

EXAMPLE_AND_INSTRUCTION = """

{format_example}


# Instruction: Based on the actual code, follow one of the "Code Review Format example".
- Note the code filename should be `{filename}`. Return the only ONE file `{filename}` under review.

## Code Review: Ordered List. Based on the "Code to be Reviewed", provide key, clear, concise, and specific answer. If any answer is no, explain how to fix it step by step.
1. Is the code implemented as per the requirements? If not, how to achieve it? Analyse it step by step.
2. Is the code logic completely correct? If there are errors, please indicate how to correct them.
3. Does the existing code follow the "Data structures and interfaces"?
4. Are all functions implemented? If there is no implementation, please indicate how to achieve it step by step.
5. Have all necessary pre-dependencies been imported? If not, indicate which ones need to be imported
6. Are methods from other files being reused correctly?

## Actions: Ordered List. Things that should be done after CR, such as implementing class A and function B

## Code Review Result: str. If the code doesn't have bugs, we don't need to rewrite it, so answer LGTM and stop. ONLY ANSWER LGTM/LBTM.
LGTM/LBTM

"""

FORMAT_EXAMPLE = """
-----

# Code Review Format example 1
## Code Review: {filename}
1. No, we should fix the logic of class A due to ...
2. ...
3. ...
4. No, function B is not implemented, ...
5. ...
6. ...

## Actions
1. Fix the `handle_events` method to update the game state only if a move is successful.
   ```python
   def handle_events(self):
       for event in pygame.event.get():
           if event.type == pygame.QUIT:
               return False
           if event.type == pygame.KEYDOWN:
               moved = False
               if event.key == pygame.K_UP:
                   moved = self.game.move('UP')
               elif event.key == pygame.K_DOWN:
                   moved = self.game.move('DOWN')
               elif event.key == pygame.K_LEFT:
                   moved = self.game.move('LEFT')
               elif event.key == pygame.K_RIGHT:
                   moved = self.game.move('RIGHT')
               if moved:
                   # Update the game state only if a move was successful
                   self.render()
       return True
   ```
2. Implement function B

## Code Review Result
LBTM

-----

# Code Review Format example 2
## Code Review: {filename}
1. Yes.
2. Yes.
3. Yes.
4. Yes.
5. Yes.
6. Yes.

## Actions
pass

## Code Review Result
LGTM

-----
"""

REWRITE_CODE_TEMPLATE = """
# Instruction: rewrite the `{filename}` based on the Code Review and Actions
## Rewrite Code: CodeBlock. If it still has some bugs, rewrite {filename} using a Markdown code block, with the filename docstring preceding the code block. Do your utmost to optimize THIS SINGLE FILE. Return all completed codes and prohibit the return of unfinished codes.
```python
## {filename}
...
```
or
```javascript
// {filename}
...
```
"""


class WriteCodeReview(Action):
    name: str = "WriteCodeReview"
    i_context: CodingContext = Field(default_factory=CodingContext)
    repo: Optional[ProjectRepo] = Field(default=None, exclude=True)
    input_args: Optional[BaseModel] = Field(default=None, exclude=True)

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
    async def write_code_review_and_rewrite(self, context_prompt, cr_prompt, doc):
        filename = doc.filename
        cr_rsp = await self._aask(context_prompt + cr_prompt)
        result = CodeParser.parse_block("Code Review Result", cr_rsp)
        if "LGTM" in result:
            return result, None

        # if LBTM, rewrite code
        async with EditorReporter(enable_llm_stream=True) as reporter:
            await reporter.async_report(
                {"type": "code", "filename": filename, "src_path": doc.root_relative_path}, "meta"
            )
            rewrite_prompt = f"{context_prompt}\n{cr_rsp}\n{REWRITE_CODE_TEMPLATE.format(filename=filename)}"
            code_rsp = await self._aask(rewrite_prompt)
            code = CodeParser.parse_code(text=code_rsp)
            doc.content = code
            await reporter.async_report(doc, "document")
        return result, code

    async def run(self, *args, **kwargs) -> CodingContext:
        iterative_code = self.i_context.code_doc.content
        k = self.context.config.code_validate_k_times or 1

        for i in range(k):
            format_example = FORMAT_EXAMPLE.format(filename=self.i_context.code_doc.filename)
            task_content = self.i_context.task_doc.content if self.i_context.task_doc else ""
            code_context = await WriteCode.get_codes(
                self.i_context.task_doc,
                exclude=self.i_context.filename,
                project_repo=self.repo,
                use_inc=self.config.inc,
            )

            ctx_list = [
                "## System Design\n" + str(self.i_context.design_doc) + "\n",
                "## Task\n" + task_content + "\n",
                "## Code Files\n" + code_context + "\n",
            ]
            if self.config.inc:
                requirement_doc = await Document.load(filename=self.input_args.requirements_filename)
                insert_ctx_list = [
                    "## User New Requirements\n" + str(requirement_doc) + "\n",
                    "## Code Plan And Change\n" + str(self.i_context.code_plan_and_change_doc) + "\n",
                ]
                ctx_list = insert_ctx_list + ctx_list

            context_prompt = PROMPT_TEMPLATE.format(
                context="\n".join(ctx_list),
                code=iterative_code,
                filename=self.i_context.code_doc.filename,
            )
            cr_prompt = EXAMPLE_AND_INSTRUCTION.format(
                format_example=format_example,
                filename=self.i_context.code_doc.filename,
            )
            len1 = len(iterative_code) if iterative_code else 0
            len2 = len(self.i_context.code_doc.content) if self.i_context.code_doc.content else 0
            logger.info(
                f"Code review and rewrite {self.i_context.code_doc.filename}: {i + 1}/{k} | len(iterative_code)={len1}, "
                f"len(self.i_context.code_doc.content)={len2}"
            )
            result, rewrited_code = await self.write_code_review_and_rewrite(
                context_prompt, cr_prompt, self.i_context.code_doc
            )
            if "LBTM" in result:
                iterative_code = rewrited_code
            elif "LGTM" in result:
                self.i_context.code_doc.content = iterative_code
                return self.i_context
        # code_rsp = await self._aask_v1(prompt, "code_rsp", OUTPUT_MAPPING)
        # self._save(context, filename, code)
        # 如果rewrited_code是None（原code perfect），那么直接返回code
        self.i_context.code_doc.content = iterative_code
        return self.i_context


@register_tool(include_functions=["run"])
class ValidateAndRewriteCode(Action):
    """According to the design and task documents, validate the code to ensure it is complete and correct."""

    name: str = "ValidateAndRewriteCode"

    async def run(
        self,
        code_path: str,
        system_design_input: str = "",
        project_schedule_input: str = "",
        code_validate_k_times: int = 2,
    ) -> str:
        """Validates the provided code based on the accompanying system design and project schedule documentation, return the complete and correct code.

        Read the code from code_path, and write the final code to code_path.
        If both system_design_input and project_schedule_input are absent, it will return and do nothing.

        Args:
            code_path (str): The file path of the code snippet to be validated. This should be a string containing the path to the source code file.
            system_design_input (str): Content or file path of the design document associated with the code. This should describe the system architecture, used in the code. It helps provide context for the validation process.
            project_schedule_input (str): Content or file path of the task document describing what the code is intended to accomplish. This should outline the functional requirements or objectives of the code.
            code_validate_k_times (int, optional): The number of iterations for validating and potentially rewriting the code. Defaults to 2.

        Returns:
            str: The potentially corrected or approved code after validation.

        Example Usage:
            # Example of how to call the run method with a code snippet and documentation
            await ValidateAndRewriteCode().run(
                code_path="/tmp/game.js",
                system_design_input="/tmp/system_design.json",
                project_schedule_input="/tmp/project_task_list.json"
            )
        """
        if not system_design_input and not project_schedule_input:
            logger.info(
                "Both `system_design_input` and `project_schedule_input` are absent, ValidateAndRewriteCode will do nothing."
            )
            return

        code, design_doc, task_doc = await asyncio.gather(
            aread(code_path), self._try_aread(system_design_input), self._try_aread(project_schedule_input)
        )
        code_doc = self._create_code_doc(code_path=code_path, code=code)
        review_action = WriteCodeReview(i_context=CodingContext(filename=code_doc.filename))

        context = "\n".join(
            [
                "## System Design\n" + design_doc + "\n",
                "## Task\n" + task_doc + "\n",
            ]
        )

        for i in range(code_validate_k_times):
            context_prompt = PROMPT_TEMPLATE.format(context=context, code=code, filename=code_path)
            cr_prompt = EXAMPLE_AND_INSTRUCTION.format(
                format_example=FORMAT_EXAMPLE.format(filename=code_path),
            )
            logger.info(f"The {i+1}th time to CodeReview: {code_path}.")
            result, rewrited_code = await review_action.write_code_review_and_rewrite(
                context_prompt, cr_prompt, doc=code_doc
            )

            if "LBTM" in result:
                code = rewrited_code
            elif "LGTM" in result:
                break

        await awrite(filename=code_path, data=code)

        return (
            f"The review and rewriting of the code in the file '{os.path.basename(code_path)}' has been completed."
            + code
        )

    @staticmethod
    async def _try_aread(input: str) -> str:
        """Try to read from the path if it's a file; return input directly if not."""

        if os.path.exists(input):
            return await aread(input)

        return input

    @staticmethod
    def _create_code_doc(code_path: str, code: str) -> Document:
        """Create a Document to represent the code doc."""

        path = Path(code_path)

        return Document(root_path=str(path.parent), filename=path.name, content=code)
