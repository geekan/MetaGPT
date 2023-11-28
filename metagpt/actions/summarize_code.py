#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : alexanderwu
@File    : summarize_code.py
"""

from tenacity import retry, stop_after_attempt, wait_fixed

from metagpt.actions.action import Action
from metagpt.config import CONFIG
from metagpt.logs import logger
from metagpt.utils.file_repository import FileRepository

PROMPT_TEMPLATE = """
NOTICE
Role: You are a professional software engineer, and your main task is to review the code.
Language: Please use the same language as the user requirement, but the title and code should be still in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

-----
# System Design
```text
{system_design}
```
-----
# Tasks
```text
{tasks}
```
-----
{code_blocks}

## Code Review All: 请你对历史所有文件进行阅读，在文件中找到可能的bug，如函数未实现、调用错误、未引用等

## Call flow: mermaid代码，根据实现的函数，使用mermaid绘制完整的调用链

## Summary: 根据历史文件的实现情况进行总结

## TODOs: Python dict[str, str]，这里写出需要修改的文件列表与理由，我们会在之后进行修改

"""

FORMAT_EXAMPLE = """

## Code Review All

### a.py
- 它少实现了xxx需求...
- 字段yyy没有给出...
- ...

### b.py
...

### c.py
...

## Call flow
```mermaid
flowchart TB
    c1-->a2
    subgraph one
    a1-->a2
    end
    subgraph two
    b1-->b2
    end
    subgraph three
    c1-->c2
    end
```

## Summary
- a.py:...
- b.py:...
- c.py:...
- ...

## TODOs
{
    "a.py": "implement requirement xxx...",
}

"""


class SummarizeCode(Action):
    def __init__(self, name="SummarizeCode", context=None, llm=None):
        super().__init__(name, context, llm)

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    async def summarize_code(self, prompt):
        code_rsp = await self._aask(prompt)
        return code_rsp

    async def run(self):
        design_doc = await FileRepository.get_file(self.context.design_filename)
        task_doc = await FileRepository.get_file(self.context.task_filename)
        src_file_repo = CONFIG.git_repo.new_file_repository(relative_path=CONFIG.src_workspace)
        code_blocks = []
        for filename in self.context.codes_filenames:
            code_doc = await src_file_repo.get(filename)
            code_block = f"```python\n{code_doc.content}\n```\n-----"
            code_blocks.append(code_block)
        format_example = FORMAT_EXAMPLE
        prompt = PROMPT_TEMPLATE.format(
            system_design=design_doc.content,
            tasks=task_doc.content,
            code_blocks="\n".join(code_blocks),
            format_example=format_example,
        )
        logger.info("Summarize code..")
        rsp = await self.summarize_code(prompt)
        return rsp
