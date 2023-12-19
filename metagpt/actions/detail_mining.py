#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/9/12 17:45
@Author  : fisherdeng
@File    : detail_mining.py
"""
from metagpt.actions import Action
from metagpt.actions.action_node import ActionNode

CONTEXT_TEMPLATE = """
## TOPIC
{topic}

## RECORD
{record}
"""

QUESTIONS = ActionNode(
    key="Questions",
    expected_type=list[str],
    instruction="Task: Refer to the context to further inquire about the details that interest you, within a word limit"
    " of 150 words. Please provide the specific details you would like to inquire about here",
    example=["1. What ...", "2. How ...", "3. ..."],
)


class DetailMining(Action):
    """This class allows LLM to further mine noteworthy details based on specific "##TOPIC"(discussion topic) and
    "##RECORD" (discussion records), thereby deepening the discussion."""

    async def run(self, topic, record):
        context = CONTEXT_TEMPLATE.format(topic=topic, record=record)
        rsp = await QUESTIONS.fill(context=context, llm=self.llm)
        return rsp
