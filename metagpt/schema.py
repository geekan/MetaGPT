#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/8 22:12
@Author  : alexanderwu
@File    : schema.py
"""

from dataclasses import dataclass, field
from typing import Type, TypedDict, Union, Optional

from pydantic import BaseModel, Field
from pydantic.main import ModelMetaclass

from metagpt.logs import logger
from metagpt.utils.serialize import actionoutout_schema_to_mapping, actionoutput_mapping_to_str, \
    actionoutput_str_to_mapping
from metagpt.utils.utils import import_class


class RawMessage(TypedDict):
    content: str
    role: str


class Message(BaseModel):
    content: str = ""
    instruct_content: BaseModel = Field(default=None)
    role: str = "user"  # system / user / assistant
    cause_by: Type["Action"] = Field(default=None)
    sent_from: str = ""
    send_to: str = ""
    restricted_to: str = ""

    def __init__(self, **kwargs):
        instruct_content = kwargs.get("instruct_content", None)
        cause_by = kwargs.get("cause_by", None)
        if instruct_content and not isinstance(instruct_content, BaseModel):
            ic = instruct_content
            mapping = actionoutput_str_to_mapping(ic["mapping"])

            actionoutput_class = import_class("ActionOutput", "metagpt.actions.action_output")
            ic_obj = actionoutput_class.create_model_class(class_name=ic["class"], mapping=mapping)
            ic_new = ic_obj(**ic["value"])
            kwargs["instruct_content"] = ic_new
        if cause_by and not isinstance(cause_by, ModelMetaclass):
            action_class = import_class("Action", "metagpt.actions.action")
            kwargs["cause_by"] = action_class.deser_class(cause_by)
        super(Message, self).__init__(**kwargs)

    def dict(self, *args, **kwargs) -> "DictStrAny":
        """ overwrite the `dict` to dump dynamic pydantic model"""
        obj_dict = super(Message, self).dict(*args, **kwargs)
        ic = self.instruct_content  # deal custom-defined action
        if ic:
            schema = ic.schema()
            mapping = actionoutout_schema_to_mapping(schema)
            mapping = actionoutput_mapping_to_str(mapping)

            obj_dict["instruct_content"] = {"class": schema["title"], "mapping": mapping, "value": ic.dict()}
        cb = self.cause_by
        if cb:
            obj_dict["cause_by"] = cb.ser_class()
        return obj_dict

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
