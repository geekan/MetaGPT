#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : write_code_review.py
@Modified By: mashenquan, 2023/11/27. Following the think-act principle, solidify the task parameters when creating the
        WriteCode object, rather than passing them in when calling the run function.
"""

from tenacity import retry, stop_after_attempt, wait_random_exponential

from metagpt.actions.action import Action
from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.schema import CodingContext
from metagpt.utils.common import CodeParser

PROMPT_TEMPLATE = """
NOTICE
Role: You are a professional software engineer, and your main task is to review the code. You need to ensure that the code conforms to the PEP8 standards, is elegantly designed and modularized, easy to read and maintain, and is written in Python 3.9 (or in another programming language).
Language: Please use the same language as the user requirement, but the title and code should be still in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

# Context
{context}

## Code to be Reviewed: {filename}
```
{code}
```

-----

## Code Review: Based on the "Code to be Reviewed", provide key, clear, concise, and specific code modification suggestions, up to 5.
1. Is the code implemented as per the requirements? If not, how to achieve it? Analyse it step by step.
2. Is the code logic completely correct? If there are errors, please indicate how to correct them.
3. Does the existing code follow the "Data structures and interfaces"?
4. Are all functions implemented? If there is no implementation, please indicate how to achieve it step by step.
5. Have all necessary pre-dependencies been imported? If not, indicate which ones need to be imported
6. Is the code implemented concisely enough? Are methods from other files being reused correctly?

## Code Review Result: If the code doesn't have bugs, we don't need to rewrite it, so answer LGTM and stop. ONLY ANSWER LGTM/LBTM.
LGTM/LBTM

## Rewrite Code: if it still has some bugs, rewrite {filename} based on "Code Review" with triple quotes, try to get LGTM. Do your utmost to optimize THIS SINGLE FILE. Implement ALL TODO. RETURN ALL CODE, NEVER OMIT ANYTHING. 以任何方式省略代码都是不允许的。
```
```

## Format example
{format_example}

"""

FORMAT_EXAMPLE = """
-----
# EXAMPLE 1
## Code Review: {filename}
1. No, we should add the logic of ...
2. ...
3. ...
4. ...
5. ...
6. ...

## Code Review Result: {filename}
LBTM

## Rewrite Code: {filename}
```python
## {filename}
...
```
-----
# EXAMPLE 2
## Code Review: {filename}
1. Yes.
2. Yes.
3. Yes.
4. Yes.
5. Yes.
6. Yes.

## Code Review Result: {filename}
LGTM

## Rewrite Code: {filename}
pass
-----
"""


class WriteCodeReview(Action):
    def __init__(self, name="WriteCodeReview", context=None, llm=None):
        super().__init__(name, context, llm)

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
    async def write_code_review_and_rewrite(self, prompt):
        code_rsp = await self._aask(prompt)
        result = CodeParser.parse_block("Code Review Result", code_rsp)
        if "LGTM" in result:
            return result, None
        code = CodeParser.parse_code(block="", text=code_rsp)
        return result, code

    async def run(self, *args, **kwargs) -> CodingContext:
        iterative_code = self.context.code_doc.content
        k = CONFIG.code_review_k_times or 1
        for i in range(k):
            format_example = FORMAT_EXAMPLE.format(filename=self.context.code_doc.filename)
            task_content = self.context.task_doc.content if self.context.task_doc else ""
            context = "\n----------\n".join(
                [
                    "```text\n" + self.context.design_doc.content + "```\n",
                    "```text\n" + task_content + "```\n",
                    "```python\n" + self.context.code_doc.content + "```\n",
                ]
            )
            prompt = PROMPT_TEMPLATE.format(
                context=context,
                code=iterative_code,
                filename=self.context.code_doc.filename,
                format_example=format_example,
            )
            logger.info(
                f"Code review and rewrite {self.context.code_doc.filename,}: {i+1}/{k} | {len(iterative_code)=}, {len(self.context.code_doc.content)=}"
            )
            result, rewrited_code = await self.write_code_review_and_rewrite(prompt)
            if "LBTM" in result:
                iterative_code = rewrited_code
            elif "LGTM" in result:
                self.context.code_doc.content = iterative_code
                return self.context
        # code_rsp = await self._aask_v1(prompt, "code_rsp", OUTPUT_MAPPING)
        # self._save(context, filename, code)
        # 如果rewrited_code是None（原code perfect），那么直接返回code
        self.context.code_doc.content = iterative_code
        return self.context
