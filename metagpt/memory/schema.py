#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the memory schema definition

from datetime import datetime
from enum import Enum
from typing import Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MemNodeType(Enum):
    OBSERVE = "observe"  # memory from observation
    THINK = "think"  # memory from self-think/reflect


class MemoryNode(BaseModel):
    """base unit of memory abstraction"""

    mem_node_id: UUID = Field(default_factory=uuid4(), description="unique node id")
    parent_node_id: Optional[str] = Field(default=None, description="memory's parent memory node id")
    node_type: MemNodeType = Field(default=MemNodeType.OBSERVE, description="memory node type")

    content: str = Field(default="", description="the memory content")
    summary: Optional[str] = Field(default=None, description="the summary of the content by providers")
    keywords: list[str] = Field(default=[], description="the extracted keywords of the content")
    embedding: list[float] = Field(default=[], description="the embeeding of the content")

    raw_path: Optional[str] = Field(default=None, description="the relative path of the media like image")
    raw_corpus: list[Union[str, dict, tuple]] = Field(default=[], description="the raw corpus of the memory")

    create_at: datetime = Field(default_factory=datetime, description="the memory create time")
    access_at: datetime = Field(default_factory=datetime, description="the memory last access time")
    expire_at: datetime = Field(default_factory=datetime, description="the memory expire time due to a TTL")

    importance: int = Field(default=0, ge=0, le=10, description="the memory importance")
    access_cnt: int = Field(default=0, description="the memory acess count time")

    @classmethod
    def create_mem_node(
        cls,
        content: str,
        summary: Optional[str] = None,
        keywords: list[str] = [],
        node_type: MemNodeType = MemNodeType.OBSERVE,
    ):
        pass

    @classmethod
    def create_mem_node_from_message(cls, message: "Message"):
        pass


class MemorySegment(BaseModel):
    """segment abstraction to store memory_node"""

    mem_nodes: list[MemoryNode] = Field(default=[], description="memory list to store MemoryNode")

    def add_mem_node(self, mem_node: MemoryNode):
        self.mem_nodes.append(mem_node)
