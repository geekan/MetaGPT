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


class Chapter(BaseModel):
    name: str = Field(default="Chapter 1", description="The name of the chapter.")
    content: str = Field(default="...", description="The content of the chapter. No more than 1000 words.")


class Chapters(BaseModel):
    chapters: List[Chapter] = Field(
        default=[
            {"name": "Chapter 1", "content": "..."},
            {"name": "Chapter 2", "content": "..."},
            {"name": "Chapter 3", "content": "..."},
        ],
        description="The chapters of the novel.",
    )


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


async def generate_novel():
    instruction = (
        "Write a novel named 'Reborn in Skyrim'. "
        "Fill the empty nodes with your own ideas. Be creative! Use your own words!"
        "I will tip you $100,000 if you write a good novel."
    )
    novel_node = await ActionNode.from_pydantic(Novel).fill(context=instruction, llm=LLM())
    chap_node = await ActionNode.from_pydantic(Chapters).fill(
        context=f"### instruction\n{instruction}\n### novel\n{novel_node.content}", llm=LLM()
    )
    print(chap_node.instruct_content)


asyncio.run(generate_novel())
