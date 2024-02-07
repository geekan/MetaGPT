#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/2/6 22:44
@Author  : femto Zheng
@File    : test_define.py
"""
from typing import List

import pytest
from pydantic import BaseModel, Field

from metagpt.actions.action_node import ActionNode
from metagpt.actions.define import (
    ActionNodeClassNode,
    CallActionNode,
    ConstantNode,
    Define,
    ForeachNode,
    IfNode,
    LoopNode,
    SymbolTable,
    SymbolTemplate,
)


class GenerateArticleNode:
    def __init__(self, context, loop_var):
        self.context = context
        self.loop_var = loop_var

    def execute(self, context):
        str = self.context.format(**context)
        context[f"article {context.get(self.loop_var, '')}"] = str
        return str


@pytest.mark.asyncio
async def test_define_generate_paragraph():
    # Create a ConstantNode with input_data of 5
    constant_node = ConstantNode(5)

    # Create a GenerateArticleNode
    generate_article_node = GenerateArticleNode(context="paragraph {i}", loop_var="i")

    # Create an IfNode with the ConstantNode as the condition and the GenerateArticleNode as the action_node
    if_node = IfNode(condition=constant_node, action_node=generate_article_node)

    # Execute the IfNode
    print(if_node.compute(context={"i": "chapter 1"}))

    # Create a GenerateArticleNode
    generate_article_node = GenerateArticleNode(context="paragraph {i}", loop_var="i")

    # Create a LoopNode with a range of 1 to 3 and the GenerateArticleNode as the action_node
    loop_node = LoopNode(range_start=1, range_end=3, action_node=generate_article_node, loop_var="i")

    # Execute the LoopNode
    result = loop_node.execute(context={"i": "chapter"})
    for para in result:
        print(para)

    generate_article_node = GenerateArticleNode(context="paragraph {i}", loop_var="i")
    foreach_node = ForeachNode(items=["chap1", "chap2", "chap3"], action_node=generate_article_node, loop_var="i")

    result = foreach_node.execute(context={"i": "chapter"})
    for para in result:
        print(para)


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


@pytest.mark.asyncio
async def test_define_generate_paragraphs():
    symbols = {
        "instruction": "Write a novel named 'Harry Potter in The Lord of the Rings'. "
        "Fill the empty nodes with your own ideas. Be creative! Use your own words!"
        "I will tip you $100,000 if you write a good novel."
    }
    symbols = SymbolTable(symbols)
    define = Define()
    novel_node = ActionNode.from_pydantic(Novel)
    define.add_node(CallActionNode(novel_node, context_symbol=SymbolTemplate("{instruction}")))
    define.add_node(
        ForeachNode(
            "outlines",
            novel_node,
            ActionNodeClassNode(
                Chapter,
                context_symbol=SymbolTemplate(
                    "### instruction\n{instruction}\n### novel\n{Novel.content}, write chapter {i}"
                ),
            ),
        )
    )
    await define.run(symbols)
    print(symbols)  # now symbol contains Novel and All Chapters
    # define.add_node(CallActionNode(chap_node))
