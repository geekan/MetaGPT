#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/8 22:12
@Author  : alexanderwu
@File    : schema.py
@Desc    : mashenquan, 2023/8/22. Add tags to enable custom message classification.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Type, TypedDict, Set, Optional, List

from pydantic import BaseModel

from metagpt.logs import logger


class MessageTag(Enum):
    Prerequisite = "prerequisite"


class RawMessage(TypedDict):
    content: str
    role: str


@dataclass
class Message:
    """list[<role>: <content>]"""
    content: str
    instruct_content: BaseModel = field(default=None)
    role: str = field(default='user')  # system / user / assistant
    cause_by: Type["Action"] = field(default="")
    sent_from: str = field(default="")
    send_to: str = field(default="")
    tags: Optional[Set] = field(default=None)

    def __str__(self):
        # prefix = '-'.join([self.role, str(self.cause_by)])
        return f"{self.role}: {self.content}"

    def __repr__(self):
        return self.__str__()

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content
        }

    def add_tag(self, tag):
        if self.tags is None:
            self.tags = set()
        self.tags.add(tag)

    def remove_tag(self, tag):
        if self.tags is None or tag not in self.tags:
            return
        self.tags.remove(tag)

    def is_contain_tags(self, tags: list) -> bool:
        """Determine whether the message contains tags."""
        if not tags or not self.tags:
            return False
        intersection = set(tags) & self.tags
        return len(intersection) > 0


@dataclass
class UserMessage(Message):
    """便于支持OpenAI的消息
       Facilitate support for OpenAI messages
    """

    def __init__(self, content: str):
        super().__init__(content, 'user')


@dataclass
class SystemMessage(Message):
    """便于支持OpenAI的消息
       Facilitate support for OpenAI messages
    """

    def __init__(self, content: str):
        super().__init__(content, 'system')


@dataclass
class AIMessage(Message):
    """便于支持OpenAI的消息
       Facilitate support for OpenAI messages
    """

    def __init__(self, content: str):
        super().__init__(content, 'assistant')



if __name__ == '__main__':
    test_content = 'test_message'
    msgs = [
        UserMessage(test_content),
        SystemMessage(test_content),
        AIMessage(test_content),
        Message(test_content, role='QA')
    ]
    logger.info(msgs)
