#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/11/20
@Author  : mashenquan
@File    : git_repository.py
@Desc: PrepareDocuments Action: initialize project folder and add new requirements to docs/requirements.txt.
        RFC 135 2.2.3.5.1.
"""
from metagpt.actions import Action


class PrepareDocuments(Action):
    def __init__(self, name="", context=None, llm=None):
        super().__init__(name, context, llm)

    async def run(self, with_message, **kwargs):
        parent = self.context.get("parent")
        if not parent:
            raise ValueError("Invalid owner")
        env = parent.get_env()
        if env.git_repository:
            return
        env.git_repository = GitRepository()
        env.git_repository.open(WORKS)
