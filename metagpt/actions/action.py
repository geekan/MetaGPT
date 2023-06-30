#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : action.py
"""
from typing import Optional
from abc import ABC

from metagpt.llm import LLM


class Action(ABC):
    def __init__(self, name: str = '', context=None, llm: LLM = None):
        self.name: str = name
        if llm is None:
            llm = LLM()
        self.llm = llm
        self.context = context
        self.prefix = ""
        self.profile = ""
        self.desc = ""

    def set_prefix(self, prefix, profile):
        """Set prefix for later usage"""
        self.prefix = prefix
        self.profile = profile

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__str__()

    async def _aask(self, prompt: str, system_msgs: Optional[list[str]] = None) -> str:
        """Append default prefix"""
        if not system_msgs:
            system_msgs = []
        system_msgs.append(self.prefix)
        return await self.llm.aask(prompt, system_msgs)

    async def run(self, *args, **kwargs):
        """Run action"""
        raise NotImplementedError("The run method should be implemented in a subclass.")
