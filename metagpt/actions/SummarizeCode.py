#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : alexanderwu
@File    : SummarizeCode.py
"""

from tenacity import retry, stop_after_attempt, wait_fixed
from metagpt.actions.action import Action
from metagpt.logs import logger
from metagpt.schema import Message

PROMPT_TEMPLATE = """
NOTICE
Role: You are a professional software engineer, and your main task is to review the code.
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

-----
# Context
{context}
-----

## Code Review All: 请你对历史所有文件进行阅读，分析每个文件是否都完整实现了用户需求，找到可能的bug，如函数未实现、调用错误、未引用等

## Call flow: 根据实现的函数，使用mermaid绘制完整的调用链

## Summary: 根据历史文件的实现情况进行总结

## TODOs: 这里写出需要修改的文件列表，我们会在之后进行修改

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
1. ...
2. ...
3. ...

"""


class SummarizeCode(Action):
    def __init__(self, name="SummaryCode", context: list[Message] = None, llm=None):
        super().__init__(name, context, llm)

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    async def summarize_code(self, prompt):
        code_rsp = await self._aask(prompt)
        return code_rsp

    async def run(self, context):
        format_example = FORMAT_EXAMPLE.format()
        prompt = PROMPT_TEMPLATE.format(context=context, format_example=format_example)
        logger.info("Code review all..")
        rsp = await self.summarize_code(prompt)
        return rsp
