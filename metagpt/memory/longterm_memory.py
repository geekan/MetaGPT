#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the implement of Long-term memory


from typing import Optional

from pydantic import ConfigDict, Field

from metagpt.logs import logger
from metagpt.memory import Memory
from metagpt.memory.memory_storage import MemoryStorage
from metagpt.roles.role import RoleContext
from metagpt.schema import Message


class LongTermMemory(Memory):
    """The Long-term memory for Roles.

    This class is responsible for managing the long-term memory of roles, including recovery and update of memory.

    Attributes:
        model_config: Configuration dictionary allowing arbitrary types.
        memory_storage: Storage for memory, defaults to a new MemoryStorage instance.
        rc: Optional RoleContext instance, default is None.
        msg_from_recover: Boolean indicating if the message is from recovery, default is False.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    memory_storage: MemoryStorage = Field(default_factory=MemoryStorage)
    rc: Optional[RoleContext] = None
    msg_from_recover: bool = False

    def recover_memory(self, role_id: str, rc: RoleContext):
        """Recover memory for a given role.

        Args:
            role_id: The identifier of the role.
            rc: The RoleContext instance.
        """
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
        """Add a message to the memory.

        Args:
            message: The message to be added.
        """
        super().add(message)
        for action in self.rc.watch:
            if message.cause_by == action and not self.msg_from_recover:
                # currently, only add role's watching messages to its memory_storage
                # and ignore adding messages from recover repeatedly
                self.memory_storage.add(message)

    def find_news(self, observed: list[Message], k=0) -> list[Message]:
        """Find news (previously unseen messages) from the most recent k memories.

        Args:
            observed: A list of observed messages.
            k: The number of recent memories to consider, defaults to 0 which means all memories.

        Returns:
            A list of previously unseen messages.
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
        """Delete a message from the memory.

        Args:
            message: The message to be deleted.
        """
        super().delete(message)
        # TODO delete message in memory_storage

    def clear(self):
        """Clear the memory."""
        super().clear()
        self.memory_storage.clean()
