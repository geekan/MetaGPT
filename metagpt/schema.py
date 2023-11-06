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
from typing import Dict, List, Set, TypedDict

from pydantic import BaseModel, Field

from metagpt.const import (
    MESSAGE_META_ROLE,
    MESSAGE_ROUTE_CAUSE_BY,
    MESSAGE_ROUTE_FROM,
    MESSAGE_ROUTE_TO,
    MESSAGE_ROUTE_TO_ALL,
)
from metagpt.logs import logger
from metagpt.utils.common import any_to_str


class RawMessage(TypedDict):
    content: str
    role: str


class Routes(BaseModel):
    """Responsible for managing routing information for the Message class."""

    routes: List[Dict] = Field(default_factory=list)

    def set_from(self, value):
        """Set the label of the message sender."""
        route = self._get_route()
        route[MESSAGE_ROUTE_FROM] = value

    def set_to(self, tags: Set):
        """Set the labels of the message recipient."""
        route = self._get_route()
        if tags:
            route[MESSAGE_ROUTE_TO] = tags
            return

        if MESSAGE_ROUTE_TO in route:
            del route[MESSAGE_ROUTE_TO]

    def add_to(self, tag: str):
        """Add a label of the message recipient."""
        route = self._get_route()
        tags = route.get(MESSAGE_ROUTE_TO, set())
        tags.add(tag)
        route[MESSAGE_ROUTE_TO] = tags

    def _get_route(self) -> Dict:
        if not self.routes:
            self.routes.append({})
        return self.routes[0]

    def is_recipient(self, tags: Set) -> bool:
        """Check if it is the message recipient."""
        route = self._get_route()
        to_tags = route.get(MESSAGE_ROUTE_TO)
        if not to_tags:
            return True

        if MESSAGE_ROUTE_TO_ALL in to_tags:
            return True
        for k in tags:
            if k in to_tags:
                return True
        return False

    @property
    def msg_from(self):
        """Message route info tells who sent this message."""
        route = self._get_route()
        return route.get(MESSAGE_ROUTE_FROM)

    @property
    def msg_to(self):
        """Labels for the consumer to filter its subscribed messages."""
        route = self._get_route()
        return route.get(MESSAGE_ROUTE_TO)

    def replace(self, old_val, new_val):
        """Replace old value with new value"""
        route = self._get_route()
        tags = route.get(MESSAGE_ROUTE_TO, set())
        tags.discard(old_val)
        tags.add(new_val)
        route[MESSAGE_ROUTE_TO] = tags


class Message(BaseModel):
    """list[<role>: <content>]"""

    content: str
    instruct_content: BaseModel = None
    meta_info: Dict = Field(default_factory=dict)
    route: Routes = Field(default_factory=Routes)

    def __init__(self, content, **kwargs):
        """
        Parameters not listed below will be stored as meta info, including custom parameters.
        :param content: Message content.
        :param instruct_content: Message content struct.
        :param meta_info: Message meta info.
        :param route: Message route configuration.
        :param msg_from: Message route info tells who sent this message.
        :param msg_to: Labels for the consumer to filter its subscribed messages.
        :param cause_by: Labels for the consumer to filter its subscribed messages, also serving as meta info.
        :param role: Message meta info tells who sent this message.
        """
        super(Message, self).__init__(
            content=content or kwargs.get("content"),
            instruct_content=kwargs.get("instruct_content"),
            meta_info=kwargs.get("meta_info", {}),
            route=kwargs.get("route", Routes()),
        )

        attribute_names = Message.__annotations__.keys()
        for k, v in kwargs.items():
            if k in attribute_names:
                continue
            if k == MESSAGE_ROUTE_FROM:
                self.set_from(any_to_str(v))
                continue
            if k == MESSAGE_ROUTE_CAUSE_BY:
                self.set_cause_by(v)
                continue
            if k == MESSAGE_ROUTE_TO:
                self.add_to(any_to_str(v))
                continue
            self.meta_info[k] = v

    def get_meta(self, key):
        """Get meta info"""
        return self.meta_info.get(key)

    def set_meta(self, key, value):
        """Set meta info"""
        self.meta_info[key] = value

    @property
    def role(self):
        """Message meta info tells who sent this message."""
        return self.get_meta(MESSAGE_META_ROLE)

    @property
    def cause_by(self):
        """Labels for the consumer to filter its subscribed messages, also serving as meta info."""
        return self.get_meta(MESSAGE_ROUTE_CAUSE_BY)

    def __setattr__(self, key, val):
        """Override `@property.setter`"""
        if key == MESSAGE_ROUTE_CAUSE_BY:
            self.set_cause_by(val)
            return
        if key == MESSAGE_ROUTE_FROM:
            self.set_from(any_to_str(val))
        super().__setattr__(key, val)

    def set_cause_by(self, val):
        """Update the value of `cause_by` in the `meta_info` and `routes` attributes."""
        old_value = self.get_meta(MESSAGE_ROUTE_CAUSE_BY)
        new_value = any_to_str(val)
        self.set_meta(MESSAGE_ROUTE_CAUSE_BY, new_value)
        self.route.replace(old_value, new_value)

    @property
    def msg_from(self):
        """Message route info tells who sent this message."""
        return self.route.msg_from

    @property
    def msg_to(self):
        """Labels for the consumer to filter its subscribed messages."""
        return self.route.msg_to

    def set_role(self, v):
        """Set the message's meta info indicating the sender."""
        self.set_meta(MESSAGE_META_ROLE, v)

    def set_from(self, v):
        """Set the message's meta info indicating the sender."""
        self.route.set_from(v)

    def set_to(self, tags: Set):
        """Set the message's meta info indicating the sender."""
        self.route.set_to(tags)

    def add_to(self, tag: str):
        """Add a subscription label for the recipients."""
        self.route.add_to(tag)

    def is_recipient(self, tags: Set):
        """Return true if any input label exists in the message's subscription labels."""
        return self.route.is_recipient(tags)

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
    def load(v):
        """Convert the json string to object."""
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


if __name__ == "__main__":
    m = Message("a", role="v1")
    m.set_role("v2")
    v = m.dump()
    m = Message.load(v)
    m.cause_by = "Message"
    m.cause_by = Routes
    m.cause_by = Routes()
    m.content = "b"

    test_content = "test_message"
    msgs = [
        UserMessage(test_content),
        SystemMessage(test_content),
        AIMessage(test_content),
        Message(test_content, role="QA"),
    ]
    logger.info(msgs)

    jsons = [
        UserMessage(test_content).dump(),
        SystemMessage(test_content).dump(),
        AIMessage(test_content).dump(),
        Message(test_content, role="QA").dump(),
    ]
    logger.info(jsons)
