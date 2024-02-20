#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the memory network to store memory segment

from pydantic import BaseModel, Field

from metagpt.memory.schema import MemoryNode, MemorySegment


class MemoryNetwork(BaseModel):
    mem_seg: MemorySegment = Field(
        default_factory=MemorySegment, description="the memory segment to store memory nodes"
    )

    def add_mem(self, mem_node: MemoryNode):
        self.mem_seg.add_mem_node(mem_node)

    def add_mems(self, mem_nodes: list[MemoryNode]):
        for mem_node in mem_nodes:
            self.add_mem(mem_node)
