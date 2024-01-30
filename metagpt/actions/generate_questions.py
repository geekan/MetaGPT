#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : generate_questions.py
"""
from metagpt.actions import Action
from metagpt.actions.action_node import ActionNode

QUESTIONS = ActionNode(
    key="Questions",
    expected_type=list[str],
    instruction="Task: Refer to the context to further inquire about the details that interest you, within a word limit"
    " of 150 words. Please provide the specific details you would like to inquire about here",
    example=["1. What ...", "2. How ...", "3. ..."],
)


class GenerateQuestions(Action):
    """This class allows LLM to further mine noteworthy details based on specific "##TOPIC"(discussion topic) and
    "##RECORD" (discussion records), thereby deepening the discussion."""

    name: str = "GenerateQuestions"

    async def run(self, context) -> ActionNode:
        return await QUESTIONS.fill(context=context, llm=self.llm)
