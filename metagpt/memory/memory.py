#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/20 12:15
@Author  : alexanderwu
@File    : memory.py
"""
from collections import defaultdict
from typing import Iterable, Type
from pathlib import Path

from metagpt.actions import Action
from metagpt.schema import Message
from metagpt.utils.utils import read_json_file, write_json_file
from metagpt.utils.serialize import serialize_general_message, deserialize_general_message


class Memory:
    """The most basic memory: super-memory"""

    def __init__(self):
        """Initialize an empty storage list and an empty index dictionary"""
        self.storage: list[Message] = []
        self.index: dict[Type[Action], list[Message]] = defaultdict(list)

    def serialize(self, stg_path: Path):
        """ stg_path = ./storage/team/environment/ or ./storage/team/environment/roles/{role_class}_{role_name}/ """
        memory_path = stg_path.joinpath("memory.json")

        storage = []
        for message in self.storage:
            # msg_dict = message.serialize()
            msg_dict = serialize_general_message(message)
            storage.append(msg_dict)

        write_json_file(memory_path, storage)

    @classmethod
    def deserialize(cls, stg_path: Path) -> "Memory":
        """ stg_path = ./storage/team/environment/ or ./storage/team/environment/roles/{role_class}_{role_name}/"""
        memory_path = stg_path.joinpath("memory.json")

        memory = Memory()
        memory_list = read_json_file(memory_path)
        for message in memory_list:
            # distinguish instruct_content type in message
            # msg = Message.deserialize(message)
            msg = deserialize_general_message(message)
            memory.add(msg)

        return memory

    def add(self, message: Message):
        """Add a new message to storage, while updating the index"""
        if message in self.storage:
            return
        self.storage.append(message)
        if message.cause_by:
            self.index[message.cause_by].append(message)

    def add_batch(self, messages: Iterable[Message]):
        for message in messages:
            self.add(message)

    def get_by_role(self, role: str) -> list[Message]:
        """Return all messages of a specified role"""
        return [message for message in self.storage if message.role == role]

    def get_by_content(self, content: str) -> list[Message]:
        """Return all messages containing a specified content"""
        return [message for message in self.storage if content in message.content]

    def delete(self, message: Message):
        """Delete the specified message from storage, while updating the index"""
        self.storage.remove(message)
        if message.cause_by and message in self.index[message.cause_by]:
            self.index[message.cause_by].remove(message)

    def clear(self):
        """Clear storage and index"""
        self.storage = []
        self.index = defaultdict(list)

    def count(self) -> int:
        """Return the number of messages in storage"""
        return len(self.storage)

    def try_remember(self, keyword: str) -> list[Message]:
        """Try to recall all messages containing a specified keyword"""
        return [message for message in self.storage if keyword in message.content]

    def get(self, k=0) -> list[Message]:
        """Return the most recent k memories, return all when k=0"""
        return self.storage[-k:]

    def find_news(self, observed: list[Message], k=0) -> list[Message]:
        """find news (previously unseen messages) from the the most recent k memories, from all memories when k=0"""
        already_observed = self.get(k)
        news: list[Message] = []
        for i in observed:
            if i in already_observed:
                continue
            news.append(i)
        return news

    def get_by_action(self, action: Type[Action]) -> list[Message]:
        """Return all messages triggered by a specified Action"""
        return self.index[action]

    def get_by_actions(self, actions: Iterable[Type[Action]]) -> list[Message]:
        """Return all messages triggered by specified Actions"""
        rsp = []
        for action in actions:
            if action not in self.index:
                continue
            rsp += self.index[action]
        return rsp
    