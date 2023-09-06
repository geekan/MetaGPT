#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/19 11:50
@Author  : alexanderwu
@File    : design_filenames.py
"""
from metagpt.actions import Action
from metagpt.logs import logger

PROMPT = """You are an AI developer, trying to write a program that generates code for users based on their intentions.
When given their intentions, provide a complete and exhaustive list of file paths needed to write the program for the user.
Only list the file paths you will write and return them as a Python string list.
Do not add any other explanations, just return a Python string list."""


class DesignFilenames(Action):
    def __init__(self, name, context=None, llm=None):
        super().__init__(name, context, llm)
        self.desc = "Based on the PRD, consider system design, and carry out the basic design of the corresponding " \
                    "APIs, data structures, and database tables. Please give your design, feedback clearly and in detail."

    async def run(self, prd):
        prompt = f"The following is the Product Requirement Document (PRD):\n\n{prd}\n\n{PROMPT}"
        design_filenames = await self._aask(prompt)
        logger.debug(prompt)
        logger.debug(design_filenames)
        return design_filenames
    