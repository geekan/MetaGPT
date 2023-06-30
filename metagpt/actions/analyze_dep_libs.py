#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/19 12:01
@Author  : alexanderwu
@File    : analyze_dep_libs.py
"""

from metagpt.actions import Action


PROMPT = """You are an AI developer, trying to write a program that generates code for users based on their intentions.

For the user's prompt:

---
The API is: {prompt}
---

We decide the generated files are: {filepaths_string}

Now that we have a file list, we need to understand the shared dependencies they have.
Please list and briefly describe the shared contents between the files we are generating, including exported variables, 
data patterns, id names of all DOM elements that javascript functions will use, message names and function names.
Focus only on the names of shared dependencies, do not add any other explanations.
"""


class AnalyzeDepLibs(Action):
    def __init__(self, name, context=None, llm=None):
        super().__init__(name, context, llm)
        self.desc = "根据上下文，分析程序运行依赖库"

    async def run(self, requirement, filepaths_string):
        # prompt = f"以下是产品需求文档(PRD):\n\n{prd}\n\n{PROMPT}"
        prompt = PROMPT.format(prompt=requirement, filepaths_string=filepaths_string)
        design_filenames = await self._aask(prompt)
        return design_filenames
