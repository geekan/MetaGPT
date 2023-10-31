#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/8 22:12
@Author  : alexanderwu
@File    : schema.py
@Modified By: mashenquan, 2023-10-31, optimize class members.
"""
from __future__ import annotations

import json
from json import JSONDecodeError
from typing import Dict, List, TypedDict

from pydantic import BaseModel, Field

from metagpt.logs import logger


class RawMessage(TypedDict):
    content: str
    role: str


class Message(BaseModel):
    """list[<role>: <content>]"""

    content: str
    instruct_content: BaseModel = None
    meta_info: Dict = Field(default_factory=dict)
    route: List[Dict] = Field(default_factory=list)

    def __init__(self, content, **kwargs):
        super(Message, self).__init__(
            content=content or kwargs.get("content"),
            instruct_content=kwargs.get("instruct_content"),
            meta_info=kwargs.get("meta_info", {}),
            route=kwargs.get("route", []),
        )

        attribute_names = Message.__annotations__.keys()
        for k, v in kwargs.items():
            if k in attribute_names:
                continue
            self.meta_info[k] = v

    def get_meta(self, key):
        return self.meta_info.get(key)

    def set_meta(self, key, value):
        self.meta_info[key] = value

    @property
    def role(self):
        return self.get_meta("role")

    @property
    def cause_by(self):
        return self.get_meta("cause_by")

    def set_role(self, v):
        self.set_meta("role", v)

    def __str__(self):
        # prefix = '-'.join([self.role, str(self.cause_by)])
        return f"{self.role}: {self.content}"

    def __repr__(self):
        return self.__str__()

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}

    def save(self) -> str:
        return self.json(exclude_none=True)

    @staticmethod
    def load(v):
        try:
            d = json.loads(v)
            return Message(**d)
        except JSONDecodeError as err:
            logger.error(f"parse json failed: {v}, error:{err}")
        return None


class UserMessage(Message):
    """便于支持OpenAI的消息
    Facilitate support for OpenAI messages
    """

    def __init__(self, content: str):
        super(Message, self).__init__(content=content, meta_info={"role": "user"})


class SystemMessage(Message):
    """便于支持OpenAI的消息
    Facilitate support for OpenAI messages
    """

    def __init__(self, content: str):
        super().__init__(content=content, meta_info={"role": "system"})


class AIMessage(Message):
    """便于支持OpenAI的消息
    Facilitate support for OpenAI messages
    """

    def __init__(self, content: str):
        super().__init__(content=content, meta_info={"role": "assistant"})


if __name__ == "__main__":
    m = Message("a", role="v1")
    m.set_role("v2")
    v = m.save()
    m = Message.load(v)

    test_content = "test_message"
    msgs = [
        UserMessage(test_content),
        SystemMessage(test_content),
        AIMessage(test_content),
        Message(test_content, role="QA"),
    ]
    logger.info(msgs)

    jsons = [
        UserMessage(test_content).save(),
        SystemMessage(test_content).save(),
        AIMessage(test_content).save(),
        Message(test_content, role="QA").save(),
    ]
    logger.info(jsons)
