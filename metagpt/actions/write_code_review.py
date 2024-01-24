#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : write_code_review.py
@Modified By: mashenquan, 2023/11/27. Following the think-act principle, solidify the task parameters when creating the
        WriteCode object, rather than passing them in when calling the run function.
"""

from pydantic import Field
from tenacity import retry, stop_after_attempt, wait_random_exponential

from metagpt.actions import WriteCode
from metagpt.actions.action import Action
from metagpt.const import CODE_PLAN_AND_CHANGE_FILENAME, REQUIREMENT_FILENAME
from metagpt.logs import logger
from metagpt.schema import CodingContext
from metagpt.utils.common import CodeParser

PROMPT_TEMPLATE = """
# System
Role: You are a professional software engineer, and your main task is to review and revise the code. You need to ensure that the code conforms to the google-style standards, is elegantly designed and modularized, easy to read and maintain.
Language: Please use the same language as the user requirement, but the title and code should be still in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

# Context
{context}

## Code to be Reviewed: {filename}
```Code
{code}
```
"""

EXAMPLE_AND_INSTRUCTION = """

{format_example}


# Instruction: Based on the actual code situation, follow one of the "Format example". Return only 1 file under review.

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
# Format example 1
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

# Format example 2
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
"""

REWRITE_CODE_TEMPLATE = """
# Instruction: rewrite code based on the Code Review and Actions
## Rewrite Code: CodeBlock. If it still has some bugs, rewrite {filename} with triple quotes. Do your utmost to optimize THIS SINGLE FILE. Return all completed codes and prohibit the return of unfinished codes.
```Code
## {filename}
...
```
"""


class WriteCodeReview(Action):
    name: str = "WriteCodeReview"
    i_context: CodingContext = Field(default_factory=CodingContext)

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
    async def write_code_review_and_rewrite(self, context_prompt, cr_prompt, filename):
        cr_rsp = await self._aask(context_prompt + cr_prompt)
        result = CodeParser.parse_block("Code Review Result", cr_rsp)
        if "LGTM" in result:
            return result, None

        # if LBTM, rewrite code
        rewrite_prompt = f"{context_prompt}\n{cr_rsp}\n{REWRITE_CODE_TEMPLATE.format(filename=filename)}"
        code_rsp = await self._aask(rewrite_prompt)
        code = CodeParser.parse_code(block="", text=code_rsp)
        return result, code

    async def run(self, *args, **kwargs) -> CodingContext:
        iterative_code = self.i_context.code_doc.content
        k = self.context.config.code_review_k_times or 1

        for i in range(k):
            format_example = FORMAT_EXAMPLE.format(filename=self.i_context.code_doc.filename)
            task_content = self.i_context.task_doc.content if self.i_context.task_doc else ""
            code_context = await WriteCode.get_codes(
                self.i_context.task_doc,
                exclude=self.i_context.filename,
                project_repo=self.repo.with_src_path(self.context.src_workspace),
                use_inc=self.config.inc,
            )

            if not self.config.inc:
                context = "\n".join(
                    [
                        "## System Design\n" + str(self.i_context.design_doc) + "\n",
                        "## Task\n" + task_content + "\n",
                        "## Code Files\n" + code_context + "\n",
                    ]
                )
            else:
                requirement_doc = await self.repo.docs.get(filename=REQUIREMENT_FILENAME)
                code_plan_and_change_doc = await self.repo.get(filename=CODE_PLAN_AND_CHANGE_FILENAME)
                context = "\n".join(
                    [
                        "## User New Requirements\n" + str(requirement_doc) + "\n",
                        "## Code Plan And Change\n" + str(code_plan_and_change_doc) + "\n",
                        "## System Design\n" + str(self.i_context.design_doc) + "\n",
                        "## Task\n" + task_content + "\n",
                        "## Code Files\n" + code_context + "\n",
                    ]
                )

            context_prompt = PROMPT_TEMPLATE.format(
                context=context,
                code=iterative_code,
                filename=self.i_context.code_doc.filename,
            )
            cr_prompt = EXAMPLE_AND_INSTRUCTION.format(
                format_example=format_example,
            )
            len1 = len(iterative_code) if iterative_code else 0
            len2 = len(self.i_context.code_doc.content) if self.i_context.code_doc.content else 0
            logger.info(
                f"Code review and rewrite {self.i_context.code_doc.filename}: {i + 1}/{k} | len(iterative_code)={len1}, "
                f"len(self.i_context.code_doc.content)={len2}"
            )
            result, rewrited_code = await self.write_code_review_and_rewrite(
                context_prompt, cr_prompt, self.i_context.code_doc.filename
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
