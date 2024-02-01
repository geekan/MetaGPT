#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/2/1 12:01
@Author  : alexanderwu
@File    : write_novel.py
"""
import asyncio
from typing import List

from pydantic import BaseModel, Field

from metagpt.actions.action_node import ActionNode
from metagpt.llm import LLM


class Novel(BaseModel):
    name: str = Field(default="The Lord of the Rings", description="The name of the novel.")
    user_group: str = Field(default="...", description="The user group of the novel.")
    outlines: List[str] = Field(
        default=["Chapter 1: ...", "Chapter 2: ...", "Chapter 3: ..."],
        description="The outlines of the novel. No more than 10 chapters.",
    )
    background: str = Field(default="...", description="The background of the novel.")
    character_names: List[str] = Field(default=["Frodo", "Gandalf", "Sauron"], description="The characters.")
    conflict: str = Field(default="...", description="The conflict of the characters.")
    plot: str = Field(default="...", description="The plot of the novel.")
    ending: str = Field(default="...", description="The ending of the novel.")
    chapter_1: str = Field(default="...", description="The content of chapter 1.")


async def generate_novel():
    instruction = "Write a novel named The Lord of the Rings. Fill the empty nodes with your own ideas."
    return await ActionNode.from_pydantic(Novel).fill(context=instruction, llm=LLM())


asyncio.run(generate_novel())
