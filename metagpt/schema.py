#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/8 22:12
@Author  : alexanderwu
@File    : schema.py
@Modified By: mashenquan, 2023-10-31. According to Chapter 2.2.1 of RFC 116:
        Replanned the distribution of responsibilities and functional positioning of `Message` class attributes.
"""
from __future__ import annotations

import asyncio
import json
from asyncio import Queue, QueueEmpty, wait_for
from json import JSONDecodeError
from typing import List, Set, TypedDict

from pydantic import BaseModel, Field

from metagpt.const import (
    MESSAGE_ROUTE_CAUSE_BY,
    MESSAGE_ROUTE_FROM,
    MESSAGE_ROUTE_TO,
    MESSAGE_ROUTE_TO_ALL,
)
from metagpt.logs import logger
from metagpt.utils.common import any_to_str, any_to_str_set


class RawMessage(TypedDict):
    content: str
    role: str


class Message(BaseModel):
    """list[<role>: <content>]"""

    content: str
    instruct_content: BaseModel = Field(default=None)
    role: str = "user"  # system / user / assistant
    cause_by: str = ""
    sent_from: str = ""
    send_to: Set = Field(default_factory={MESSAGE_ROUTE_TO_ALL})

    def __init__(
        self,
        content,
        instruct_content=None,
        role="user",
        cause_by="",
        sent_from="",
        send_to=MESSAGE_ROUTE_TO_ALL,
        **kwargs,
    ):
        """
        Parameters not listed below will be stored as meta info, including custom parameters.
        :param content: Message content.
        :param instruct_content: Message content struct.
        :param cause_by: Message producer
        :param sent_from: Message route info tells who sent this message.
        :param send_to: Labels for the consumer to filter its subscribed messages.
        :param role: Message meta info tells who sent this message.
        """
        super().__init__(
            content=content,
            instruct_content=instruct_content,
            role=role,
            cause_by=any_to_str(cause_by),
            sent_from=any_to_str(sent_from),
            send_to=any_to_str_set(send_to),
            **kwargs,
        )

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
    def load(val):
        """Convert the json string to object."""
        try:
            d = json.loads(val)
            return Message(**d)
        except JSONDecodeError as err:
            logger.error(f"parse json failed: {val}, error:{err}")
        return None


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


class MessageQueue:
    """Message queue which supports asynchronous updates."""

    def __init__(self):
        self._queue = Queue()

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
    def load(self, v) -> "MessageQueue":
        """Convert the json string to the `MessageQueue` object."""
        q = MessageQueue()
        try:
            lst = json.loads(v)
            for i in lst:
                msg = Message(**i)
                q.push(msg)
        except JSONDecodeError as e:
            logger.warning(f"JSON load failed: {v}, error:{e}")

        return q
