#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/8 22:12
@Author  : alexanderwu
@File    : schema.py
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Type, TypedDict
import copy

from pydantic import BaseModel

from metagpt.logs import logger
# from metagpt.utils.serialize import actionoutout_schema_to_mapping
# from metagpt.actions.action_output import ActionOutput
# from metagpt.actions.action import Action


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
    restricted_to: str = field(default="")

    def __str__(self):
        # prefix = '-'.join([self.role, str(self.cause_by)])
        return f"{self.role}: {self.content}"

    def __repr__(self):
        return self.__str__()

    # def serialize(self):
    #     message_cp: Message = copy.deepcopy(self)
    #     ic = message_cp.instruct_content
    #     if ic:
    #         # model create by pydantic create_model like `pydantic.main.prd`, can't pickle.dump directly
    #         schema = ic.schema()
    #         mapping = actionoutout_schema_to_mapping(schema)
    #
    #         message_cp.instruct_content = {"class": schema["title"], "mapping": mapping, "value": ic.dict()}
    #     cb = message_cp.cause_by
    #     if cb:
    #         message_cp.cause_by = cb.serialize()
    #
    #     return message_cp.dict()
    #
    # @classmethod
    # def deserialize(cls, message_dict: dict):
    #     instruct_content = message_dict.get("instruct_content")
    #     if instruct_content:
    #         ic = instruct_content
    #         ic_obj = ActionOutput.create_model_class(class_name=ic["class"], mapping=ic["mapping"])
    #         ic_new = ic_obj(**ic["value"])
    #         message_dict.instruct_content = ic_new
    #     cause_by = message_dict.get("cause_by")
    #     if cause_by:
    #         message_dict.cause_by = Action.deserialize(cause_by)
    #
    #     return Message(**message_dict)

    def dict(self):
        return {
            "content": self.content,
            "instruct_content": self.instruct_content,
            "role": self.role,
            "cause_by": self.cause_by,
            "sent_from": self.sent_from,
            "send_to": self.send_to,
            "restricted_to": self.restricted_to
        }

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content
        }


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
