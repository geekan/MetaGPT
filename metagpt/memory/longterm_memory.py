#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Desc   : the implement of Long-term memory
"""

from typing import Optional

from pydantic import ConfigDict, Field

from metagpt.logs import logger
from metagpt.memory import Memory
from metagpt.memory.memory_storage import MemoryStorage
from metagpt.roles.role import RoleContext
from metagpt.schema import Message


class LongTermMemory(Memory):
    """
    The Long-term memory for Roles
    - recover memory when it staruped
    - update memory when it changed
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    memory_storage: MemoryStorage = Field(default_factory=MemoryStorage)
    rc: Optional[RoleContext] = None
    msg_from_recover: bool = False

    def recover_memory(self, role_id: str, rc: RoleContext):
        messages = self.memory_storage.recover_memory(role_id)
        self.rc = rc
        if not self.memory_storage.is_initialized:
            logger.warning(f"It may the first time to run Agent {role_id}, the long-term memory is empty")
        else:
            logger.warning(
                f"Agent {role_id} has existing memory storage with {len(messages)} messages " f"and has recovered them."
            )
        self.msg_from_recover = True
        self.add_batch(messages)
        self.msg_from_recover = False

    def add(self, message: Message):
        super().add(message)
        for action in self.rc.watch:
            if message.cause_by == action and not self.msg_from_recover:
                # currently, only add role's watching messages to its memory_storage
                # and ignore adding messages from recover repeatedly
                self.memory_storage.add(message)

    def find_news(self, observed: list[Message], k=0) -> list[Message]:
        """
        find news (previously unseen messages) from the the most recent k memories, from all memories when k=0
            1. find the short-term memory(stm) news
            2. furthermore, filter out similar messages based on ltm(long-term memory), get the final news
        """
        stm_news = super().find_news(observed, k=k)  # shot-term memory news
        if not self.memory_storage.is_initialized:
            # memory_storage hasn't initialized, use default `find_news` to get stm_news
            return stm_news

        ltm_news: list[Message] = []
        for mem in stm_news:
            # filter out messages similar to those seen previously in ltm, only keep fresh news
            mem_searched = self.memory_storage.search_dissimilar(mem)
            if len(mem_searched) > 0:
                ltm_news.append(mem)
        return ltm_news[-k:]

    def delete(self, message: Message):
        super().delete(message)
        # TODO delete message in memory_storage

    def clear(self):
        super().clear()
        self.memory_storage.clean()
