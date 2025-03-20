#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : action.py
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class BaseAction(BaseModel):
    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__str__()

    async def _aask(self, prompt: str, system_msgs: Optional[list[str]] = None) -> str:
        """Append default prefix"""
        return await self.llm.aask(prompt, system_msgs)

    async def run(self, *args, **kwargs):
        """Run action"""
        raise NotImplementedError("The run method should be implemented in a subclass.")
