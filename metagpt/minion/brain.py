#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/13 12:29
@Author  : femto Zheng
@File    : brain.py
"""

import uuid
from datetime import datetime
from typing import Any

from jinja2 import Template
from pydantic import BaseModel

from metagpt.actions.action_node import ActionNode
from metagpt.llm import LLM
from metagpt.minion.input import Input
from metagpt.minion.minion import RouteMinion


class Mind(BaseModel):
    id: str = "UnnamedMind"
    description: str = ""
    brain: Any = None  # Brain

    async def step(self, input, run_id=None):
        input.run_id = run_id or uuid.uuid4()
        input.short_context = input.context  # first set digested context same as context

        smart = RouteMinion(input, brain=self.brain)
        answer, score = await smart.execute()
        return answer, score, False, False, {}  # terminated: false, truncated:false, info:{}


class Brain:
    def __init__(self, id=None, memory=None, llm=LLM()):
        self.id = id or uuid.uuid4()
        self.minds = {}
        self.add_mind(
            Mind(
                id="left_mind",
                description="""
I'm the left mind, adept at logical reasoning and analytical thinking. I excel in tasks involving mathematics, language, and detailed analysis. My capabilities include:

Solving complex mathematical problems
Understanding and processing language with precision
Performing logical reasoning and critical thinking
Analyzing and synthesizing information systematically
Engaging in tasks that require attention to detail and structure""",
            )
        )
        self.add_mind(
            Mind(
                id="right_mind",
                description="""
I'm the right mind, flourishing in creative and artistic tasks. I thrive in activities that involve imagination, intuition, and holistic thinking. My capabilities include:

Creating and appreciating art and music
Engaging in creative problem-solving and innovation
Understanding and interpreting emotions and expressions
Recognizing patterns and spatial relationships
Thinking in a non-linear and abstract manner""",
            )
        )

        self.add_mind(
            Mind(
                id="hippocampus_mind",
                description="""I'm the hippocampus mind, specializing in memory formation, organization, and retrieval. I play a crucial role in both the storage of new memories and the recall of past experiences. My capabilities include:

Forming and consolidating new memories
Organizing and structuring information for easy retrieval
Facilitating the recall of past experiences and learned information
Connecting new information with existing knowledge
Supporting navigation and spatial memory""",
            )
        )

        # self.add_mind(Mind(id="hypothalamus", description="..."))
        if not memory:
            pass

        # memory = Memory.from_config(config)
        memory = None
        self.mem = memory
        self.llm = llm

    def add_mind(self, mind):
        self.minds[mind.id] = mind
        mind.brain = self

    async def step(self, input=None, query="", query_type="", **kwargs):
        run_id = uuid.uuid4()

        input = input or Input(query=query, query_type=query_type, query_time=datetime.utcnow(), **kwargs)

        mind_id = await self.choose_mind(input)
        mind = self.minds[mind_id]
        return await mind.step(input, run_id)

    async def choose_mind(self, input):
        mind_template = Template(
            """
I have minds:
{% for mind in minds %}
1. **ID:** {{ mind.id }}  
   **Description:** 
   "{{ mind.description }}"
{% endfor %}
According to the current user's query, 
which is of query type: {{ input.query_type }},
and user's query: {{ input.query }}
help me choose the right mind to process the query.
return the id of the mind, please note you *MUST* return exactly case same as I provided here, do not uppercase or downcase yourself.
"""
        )

        # Create the filled template
        filled_template = mind_template.render(minds=self.minds.values(), input=input)

        node = ActionNode(
            key="mind",
            expected_type=str,
            instruction="mind id",
            example="",
        )
        node = await node.fill(
            context=filled_template,
            llm=self.llm,
        )

        return node.instruct_content.mind


Mind.update_forward_refs()
