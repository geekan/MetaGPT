#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : action.py
"""

from __future__ import annotations

from typing import Optional, Any

from pydantic import BaseModel, Field

from metagpt.llm import LLM
from metagpt.provider.base_gpt_api import BaseGPTAPI
from metagpt.schema import CodingContext, CodeSummarizeContext, TestingContext, RunCodeContext

action_subclass_registry = {}


class Action(BaseModel):
    name: str = ""
    llm: BaseGPTAPI = Field(default_factory=LLM, exclude=True)
    context: dict | CodingContext | CodeSummarizeContext | TestingContext | RunCodeContext | str | None = ""
    prefix = ""  # aask*时会加上prefix，作为system_message
    desc = ""  # for skill manager
    # node: ActionNode = Field(default_factory=ActionNode, exclude=True)

    # builtin variables
    builtin_class_name: str = ""

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

        # deserialize child classes dynamically for inherited `action`
        object.__setattr__(self, "builtin_class_name", self.__class__.__name__)
        self.__fields__["builtin_class_name"].default = self.__class__.__name__

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        action_subclass_registry[cls.__name__] = cls

    def dict(self, *args, **kwargs) -> "DictStrAny":
        obj_dict = super(Action, self).dict(*args, **kwargs)
        if "llm" in obj_dict:
            obj_dict.pop("llm")
        return obj_dict

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
