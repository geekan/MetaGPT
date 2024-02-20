#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : memory mechanism including store/retrieval/rank

from typing import Optional

from pydantic import BaseModel, Field

from metagpt.memory.memory_network import MemoryNetwork
from metagpt.memory.schema import MemoryNode
from metagpt.schema import Message


class Memory(BaseModel):
    mem_network: Optional[MemoryNetwork] = Field(
        default_factory=MemoryNetwork, description="the network to store memory"
    )

    def add_msg(self, message: Message):
        mem_node = MemoryNode.create_mem_node_from_message(message)
        self.mem_network.add_mem(mem_node)

    def add_msgs(self, messages: list[Message]):
        for msg in messages:
            self.add_msg(msg)
