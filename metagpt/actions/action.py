#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : action.py
"""

from __future__ import annotations

from abc import ABC
from typing import Optional

from metagpt.actions.action_node import ActionNode
from metagpt.llm import LLM
from metagpt.schema import BaseContext


class Action(ABC):
    """Action abstract class, requiring all inheritors to provide a series of standard capabilities"""

    name: str
    llm: LLM
    context: dict | BaseContext | str | None
    prefix: str
    desc: str
    node: ActionNode | None

    def __init__(self, name: str = "", context=None, llm: LLM = None):
        self.name: str = name
        if llm is None:
            llm = LLM()
        self.llm = llm
        self.context = context
        self.prefix = ""  # aask*时会加上prefix，作为system_message
        self.desc = ""  # for skill manager
        self.node = None

    def set_prefix(self, prefix):
        """Set prefix for later usage"""
        self.prefix = prefix
        return self

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
