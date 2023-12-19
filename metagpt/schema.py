#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/8 22:12
@Author  : alexanderwu
@File    : schema.py
@Modified By: mashenquan, 2023-10-31. According to Chapter 2.2.1 of RFC 116:
        Replanned the distribution of responsibilities and functional positioning of `Message` class attributes.
@Modified By: mashenquan, 2023/11/22.
        1. Add `Document` and `Documents` for `FileRepository` in Section 2.2.3.4 of RFC 135.
        2. Encapsulate the common key-values set to pydantic structures to standardize and unify parameter passing
        between actions.
        3. Add `id` to `Message` according to Section 2.2.3.1.1 of RFC 135.
"""

from __future__ import annotations

import asyncio
import json
import os.path
import uuid
from asyncio import Queue, QueueEmpty, wait_for
from json import JSONDecodeError
from pathlib import Path
from typing import Dict, List, Optional, Set, Type, TypedDict, TypeVar, Any

from pydantic import BaseModel, Field

from metagpt.config import CONFIG
from metagpt.const import (
    MESSAGE_ROUTE_CAUSE_BY,
    MESSAGE_ROUTE_FROM,
    MESSAGE_ROUTE_TO,
    MESSAGE_ROUTE_TO_ALL,
    SYSTEM_DESIGN_FILE_REPO,
    TASK_FILE_REPO,
)
from metagpt.logs import logger
from metagpt.utils.common import any_to_str, any_to_str_set, import_class
from metagpt.utils.serialize import actionoutout_schema_to_mapping, actionoutput_mapping_to_str, \
    actionoutput_str_to_mapping
from metagpt.utils.exceptions import handle_exception


class RawMessage(TypedDict):
    content: str
    role: str


class Document(BaseModel):
    """
    Represents a document.
    """

    root_path: str = ""
    filename: str = ""
    content: str = ""

    def get_meta(self) -> Document:
        """Get metadata of the document.

        :return: A new Document instance with the same root path and filename.
        """

        return Document(root_path=self.root_path, filename=self.filename)

    @property
    def root_relative_path(self):
        """Get relative path from root of git repository.

        :return: relative path from root of git repository.
        """
        return os.path.join(self.root_path, self.filename)

    @property
    def full_path(self):
        if not CONFIG.git_repo:
            return None
        return str(CONFIG.git_repo.workdir / self.root_path / self.filename)

    def __str__(self):
        return self.content

    def __repr__(self):
        return self.content


class Documents(BaseModel):
    """A class representing a collection of documents.

    Attributes:
        docs (Dict[str, Document]): A dictionary mapping document names to Document instances.
    """

    docs: Dict[str, Document] = Field(default_factory=dict)


class Message(BaseModel):
    """list[<role>: <content>]"""

    id: str  # According to Section 2.2.3.1.1 of RFC 135
    content: str
    instruct_content: BaseModel = Field(default=None)
    role: str = "user"  # system / user / assistant
    cause_by: str = ""
    sent_from: str = ""
    send_to: Set = Field(default_factory={MESSAGE_ROUTE_TO_ALL})

    def __init__(self, **kwargs):
        instruct_content = kwargs.get("instruct_content", None)
        if instruct_content and not isinstance(instruct_content, BaseModel):
            ic = instruct_content
            mapping = actionoutput_str_to_mapping(ic["mapping"])

            actionoutput_class = import_class("ActionOutput", "metagpt.actions.action_output")
            ic_obj = actionoutput_class.create_model_class(class_name=ic["class"], mapping=mapping)
            ic_new = ic_obj(**ic["value"])
            kwargs["instruct_content"] = ic_new

        kwargs["id"] = kwargs.get("id", uuid.uuid4().hex)
        kwargs["cause_by"] = any_to_str(kwargs.get("cause_by",
                                                   import_class("UserRequirement", "metagpt.actions.add_requirement")))
        kwargs["sent_from"] = any_to_str(kwargs.get("sent_from", ""))
        kwargs["send_to"] = any_to_str_set(kwargs.get("send_to", {MESSAGE_ROUTE_TO_ALL}))
        super(Message, self).__init__(**kwargs)

    def __setattr__(self, key, val):
        """Override `@property.setter`, convert non-string parameters into string parameters."""
        if key == MESSAGE_ROUTE_CAUSE_BY:
            new_val = any_to_str(val)
        elif key == MESSAGE_ROUTE_FROM:
            new_val = any_to_str(val)
        elif key == MESSAGE_ROUTE_TO:
            new_val = any_to_str_set(val)
        else:
            new_val = val
        super().__setattr__(key, new_val)

    def dict(self, *args, **kwargs) -> "DictStrAny":
        """ overwrite the `dict` to dump dynamic pydantic model"""
        obj_dict = super(Message, self).dict(*args, **kwargs)
        ic = self.instruct_content  # deal custom-defined action
        if ic:
            schema = ic.schema()
            mapping = actionoutout_schema_to_mapping(schema)
            mapping = actionoutput_mapping_to_str(mapping)

            obj_dict["instruct_content"] = {"class": schema["title"], "mapping": mapping, "value": ic.dict()}
        return obj_dict

    def __str__(self):
        # prefix = '-'.join([self.role, str(self.cause_by)])
        return f"{self.role}: {self.content}"

    def __repr__(self):
        return self.__str__()

    def to_dict(self) -> dict:
        """Return a dict containing `role` and `content` for the LLM call.l"""
        return {"role": self.role, "content": self.content}

    def dump(self) -> str:
        """Convert the object to json string"""
        return self.json(exclude_none=True)

    @staticmethod
    @handle_exception(exception_type=JSONDecodeError, default_return=None)
    def load(val):
        """Convert the json string to object."""
        d = json.loads(val)
        return Message(**d)


class UserMessage(Message):
    """便于支持OpenAI的消息
    Facilitate support for OpenAI messages
    """

    def __init__(self, content: str):
        super().__init__(content=content, role="user")


class SystemMessage(Message):
    """便于支持OpenAI的消息
    Facilitate support for OpenAI messages
    """

    def __init__(self, content: str):
        super().__init__(content=content, role="system")


class AIMessage(Message):
    """便于支持OpenAI的消息
    Facilitate support for OpenAI messages
    """

    def __init__(self, content: str):
        super().__init__(content=content, role="assistant")


class MessageQueue(BaseModel):
    """Message queue which supports asynchronous updates."""

    _queue: Queue = Field(default_factory=Queue)

    _private_attributes = {
        "_queue": Queue()
    }

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs: Any):
        for key in self._private_attributes.keys():
            if key in kwargs:
                object.__setattr__(self, key, kwargs[key])
            else:
                object.__setattr__(self, key, Queue())

    def pop(self) -> Message | None:
        """Pop one message from the queue."""
        try:
            item = self._queue.get_nowait()
            if item:
                self._queue.task_done()
            return item
        except QueueEmpty:
            return None

    def pop_all(self) -> List[Message]:
        """Pop all messages from the queue."""
        ret = []
        while True:
            msg = self.pop()
            if not msg:
                break
            ret.append(msg)
        return ret

    def push(self, msg: Message):
        """Push a message into the queue."""
        self._queue.put_nowait(msg)

    def empty(self):
        """Return true if the queue is empty."""
        return self._queue.empty()

    async def dump(self) -> str:
        """Convert the `MessageQueue` object to a json string."""
        if self.empty():
            return "[]"

        lst = []
        try:
            while True:
                item = await wait_for(self._queue.get(), timeout=1.0)
                if item is None:
                    break
                lst.append(item.dict(exclude_none=True))
                self._queue.task_done()
        except asyncio.TimeoutError:
            logger.debug("Queue is empty, exiting...")
        return json.dumps(lst)

    @staticmethod
    def load(i) -> "MessageQueue":
        """Convert the json string to the `MessageQueue` object."""
        queue = MessageQueue()
        try:
            lst = json.loads(i)
            for i in lst:
                msg = Message(**i)
                queue.push(msg)
        except JSONDecodeError as e:
            logger.warning(f"JSON load failed: {i}, error:{e}")

        return queue


# 定义一个泛型类型变量
T = TypeVar("T", bound="BaseModel")


class BaseContext(BaseModel):
    @staticmethod
    @handle_exception
    def loads(val: str, cls: Type[T]) -> Optional[T]:
        m = json.loads(val)
        return cls(**m)


class CodingContext(BaseContext):
    filename: str
    design_doc: Optional[Document]
    task_doc: Optional[Document]
    code_doc: Optional[Document]


class TestingContext(BaseContext):
    filename: str
    code_doc: Document
    test_doc: Optional[Document]


class RunCodeContext(BaseContext):
    mode: str = "script"
    code: Optional[str]
    code_filename: str = ""
    test_code: Optional[str]
    test_filename: str = ""
    command: List[str] = Field(default_factory=list)
    working_directory: str = ""
    additional_python_paths: List[str] = Field(default_factory=list)
    output_filename: Optional[str]
    output: Optional[str]


class RunCodeResult(BaseContext):
    summary: str
    stdout: str
    stderr: str


class CodeSummarizeContext(BaseModel):
    design_filename: str = ""
    task_filename: str = ""
    codes_filenames: List[str] = Field(default_factory=list)
    reason: str = ""

    @staticmethod
    def loads(filenames: List) -> CodeSummarizeContext:
        ctx = CodeSummarizeContext()
        for filename in filenames:
            if Path(filename).is_relative_to(SYSTEM_DESIGN_FILE_REPO):
                ctx.design_filename = str(filename)
                continue
            if Path(filename).is_relative_to(TASK_FILE_REPO):
                ctx.task_filename = str(filename)
                continue
        return ctx

    def __hash__(self):
        return hash((self.design_filename, self.task_filename))


class BugFixContext(BaseContext):
    filename: str = ""
