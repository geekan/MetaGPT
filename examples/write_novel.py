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


class Chapter(BaseModel):
    name: str = Field(default="Chapter 1", description="The name of the chapter.")
    content: str = Field(default="...", description="The content of the chapter. No more than 1000 words.")


async def generate_novel():
    instruction = (
        "Write a novel named 'Harry Potter in The Lord of the Rings'. "
        "Fill the empty nodes with your own ideas. Be creative! Use your own words!"
        "I will tip you $100,000 if you write a good novel."
    )
    novel_node = await ActionNode.from_pydantic(Novel).fill(context=instruction, llm=LLM())
    chap_node = await ActionNode.from_pydantic(Chapter).fill(
        context=f"### instruction\n{instruction}\n### novel\n{novel_node.content}", llm=LLM()
    )
    print(chap_node.content)


asyncio.run(generate_novel())
